"""
Prompt templates for Excel Q&A query generation.
"""

SYSTEM_PROMPT = """You are an expert data analyst specialized in generating Python pandas code to answer questions about Excel/CSV data.

Your task is to generate safe, efficient pandas code that answers the user's question based on the provided data context.

STRICT REQUIREMENTS:
1. Only use pandas and numpy libraries (already imported as 'pd' and 'np')
2. The DataFrame is already loaded as 'df' - DO NOT try to read files
3. Return the final result in a variable called 'result'
4. Keep code simple and readable
5. Handle missing values appropriately
6. DO NOT use any file I/O operations
7. DO NOT import any modules
8. DO NOT use eval(), exec(), or compile()
9. DO NOT access system resources or network
10. Use ONLY the column names that are provided in the DATA CONTEXT - do not assume or invent column names
11. Column names may have leading/trailing spaces (e.g., " Sales" not "Sales") - use EXACT names from the context

CODE STRUCTURE:
```python
# Your analysis code here
# Use df (the loaded DataFrame)
# Store final answer in 'result' variable
result = ...  # This will be returned to the user
```

RESPONSE FORMAT:
Return ONLY valid JSON (no markdown, no code blocks, no extra text). The JSON must have these exact fields:
{
    "code": "your_pandas_code_here",
    "explanation": "brief explanation",
    "result_type": "number|text|dataframe|list"
}

IMPORTANT: The "code" field must contain ONLY executable Python code. Do NOT include explanatory text, JSON structure, or markdown in the code field.
"""

FEW_SHOT_EXAMPLES = """
EXAMPLE 1:
Question: "What columns are available?"
Available columns: ['Product', 'Quantity', 'Price', 'Category']

Response:
{"code": "result = list(df.columns)", "explanation": "Returns list of all column names", "result_type": "list"}

EXAMPLE 2:
Question: "What is the average sales amount?"
Available columns: ['Product', 'Sales', 'Region']

Response:
{"code": "result = df['Sales'].mean()", "explanation": "Calculates the mean of the Sales column", "result_type": "number"}

EXAMPLE 3:
Question: "Show me the top 5 products by revenue"
Available columns: ['Product', 'Revenue', 'Category']

Response:
{"code": "result = df.nlargest(5, 'Revenue')[['Product', 'Revenue']]", "explanation": "Selects the 5 rows with highest Revenue", "result_type": "dataframe"}

EXAMPLE 4:
Question: "How many unique customers are there?"
Available columns: ['Customer', 'Order_ID', 'Date']

Response:
{"code": "result = df['Customer'].nunique()", "explanation": "Counts unique values in Customer column", "result_type": "number"}

EXAMPLE 5:
Question: "Group sales by region and calculate total"
Available columns: ['Region', 'Sales', 'Date']

Response:
{"code": "result = df.groupby('Region')['Sales'].sum().reset_index()", "explanation": "Groups by Region and sums Sales", "result_type": "dataframe"}
"""

CONTEXT_TEMPLATE = """
DATA CONTEXT:
- Sheet Name: {sheet_name}
- Total Rows: {row_count}
- Total Columns: {column_count}

AVAILABLE COLUMNS (use EXACT names including any spaces/special characters):
{column_info}

⚠️ CRITICAL: Column names may contain leading/trailing spaces or special characters.
Always use the EXACT column name as shown above. For example:
- If column is " Sales" (with space), use df[" Sales"] NOT df["Sales"]
- If column is "Sale Price", use df["Sale Price"] with the space

DATA QUALITY:
- Missing Values: {missing_values}
- Duplicate Rows: {duplicate_count}

SAMPLE DATA (first 5 rows):
{sample_data}

USER QUESTION:
{user_question}

Generate the pandas code to answer this question using the EXACT column names shown above.
"""


def build_column_info(sheet_metadata: dict) -> str:
    """Build formatted column information from sheet metadata."""
    columns = sheet_metadata.get("columns", [])
    column_types = sheet_metadata.get("column_types", {})
    
    column_lines = []
    for col in columns:
        # Handle columns as list of strings (current format)
        if isinstance(col, str):
            name = col
            dtype = column_types.get(col, "unknown")
        # Handle columns as list of dicts (legacy format)
        else:
            name = col.get("name", "Unknown")
            dtype = col.get("type", "unknown")
        
        line = f"- {name} ({dtype})"
        
        # For dict format, add statistics if available
        if isinstance(col, dict):
            null_count = col.get("null_count", 0)
            unique_count = col.get("unique_count", 0)
            
            # Add statistics for numeric columns
            if col.get("type") == "numeric" and "statistics" in col:
                stats = col["statistics"]
                line += f" - mean: {stats.get('mean', 'N/A'):.2f}, min: {stats.get('min', 'N/A')}, max: {stats.get('max', 'N/A')}"
            
            # Add info about nulls and unique values
            if null_count > 0:
                line += f" - {null_count} nulls"
            if unique_count > 0:
                line += f" - {unique_count} unique"
            
        column_lines.append(line)
    
    return "\n".join(column_lines) if column_lines else "No column information available"


def build_sample_data(preview_data: list) -> str:
    """Build formatted sample data string."""
    if not preview_data:
        return "No sample data available"
    
    # Take first 5 rows
    sample = preview_data[:5]
    
    # Format as a simple table
    if not sample:
        return "No sample data available"
    
    # Get all keys from first row
    headers = list(sample[0].keys()) if sample else []
    
    # Build header row
    lines = [" | ".join(headers)]
    lines.append(" | ".join(["-" * len(h) for h in headers]))
    
    # Build data rows
    for row in sample:
        values = [str(row.get(h, "")) for h in headers]
        lines.append(" | ".join(values))
    
    return "\n".join(lines)


def build_query_prompt(
    user_question: str,
    sheet_name: str,
    sheet_metadata: dict,
    preview_data: list
) -> str:
    """
    Build complete prompt for query generation.
    
    Args:
        user_question: The natural language question
        sheet_name: Name of the Excel sheet
        sheet_metadata: Sheet metadata including columns and statistics
        preview_data: Sample rows from the sheet
    
    Returns:
        Complete prompt string
    """
    column_info = build_column_info(sheet_metadata)
    sample_data = build_sample_data(preview_data)
    
    context_prompt = CONTEXT_TEMPLATE.format(
        sheet_name=sheet_name,
        row_count=sheet_metadata.get("row_count", 0),
        column_count=sheet_metadata.get("column_count", 0),
        column_info=column_info,
        missing_values=sheet_metadata.get("total_missing", 0),
        duplicate_count=sheet_metadata.get("duplicate_rows", 0),
        sample_data=sample_data,
        user_question=user_question
    )
    
    return context_prompt


def build_refinement_prompt(
    original_question: str,
    original_code: str,
    error_message: str,
    refinement_request: str
) -> str:
    """
    Build prompt for query refinement after an error or user request.
    
    Args:
        original_question: The original question
        original_code: The code that was generated
        error_message: Error message if code failed
        refinement_request: User's refinement request
    
    Returns:
        Refinement prompt string
    """
    prompt = f"""
The previous code generated for the question "{original_question}" needs refinement.

ORIGINAL CODE:
```python
{original_code}
```
"""
    
    if error_message:
        prompt += f"""
ERROR ENCOUNTERED:
{error_message}
"""
    
    prompt += f"""
REFINEMENT REQUEST:
{refinement_request}

Please generate improved code that addresses the issue or refinement request.
Follow the same format and safety requirements as before.
"""
    
    return prompt
