# Excel Q&A Assistant - Implementation Plan

**Project**: Excel Data Analysis with AI Assistant  
**Branch**: `excel-data-analysis`  
**Start Date**: October 6, 2025  
**Target Completion**: 21 days (3 weeks)

---

## 📋 Executive Summary

Building an intelligent Excel Q&A Assistant that allows users to upload Excel files and ask analytical questions in natural language. This project integrates with our existing chat infrastructure and adds advanced data analysis capabilities.

### Core Features:
1. ✅ Multi-sheet Excel file upload and parsing
2. ✅ Natural language to Pandas code generation
3. ✅ Safe sandboxed code execution
4. ✅ Dynamic chart generation with Plotly
5. ✅ Multi-format export (Excel, CSV, PNG, PDF)

---

## 🏗️ Architecture Overview

### System Integration Points:
```
┌─────────────────────────────────────────────────────────────┐
│                    Existing Infrastructure                   │
│  • User Authentication (JWT, RBAC)                          │
│  • Chat System (threads, messages)                          │
│  • Document Upload (file storage)                           │
│  • AI Integration (Claude API, LangChain)                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    New Excel Q&A Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │Excel Parser  │→ │Code Generator│→ │Visualization │     │
│  │(Pandas/      │  │(LangChain+   │  │(Plotly)      │     │
│  │ openpyxl)    │  │ Claude)      │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         ↓                  ↓                  ↓             │
│  ┌──────────────────────────────────────────────────┐     │
│  │        Sandboxed Execution Environment           │     │
│  │        (RestrictedPython + Resource Limits)      │     │
│  └──────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Dependencies to Install

### Backend
```bash
# Core Excel processing
pip install openpyxl==3.1.2
pip install xlrd==2.0.1
pip install pandas==2.1.3

# Visualization
pip install plotly==5.18.0
pip install kaleido==0.2.1

# Code sandboxing
pip install RestrictedPython==6.2

# Testing
pip install pytest-asyncio==0.21.1
```

### Frontend
```bash
# Data grid
npm install ag-grid-react@31.0.1
npm install @ag-grid-community/core@31.0.1

# Charts
npm install react-plotly.js@2.6.0
npm install plotly.js@2.27.1

# File upload
npm install react-dropzone@14.2.3
```

---

## 🗂️ New File Structure

```
backend/src/
├── infrastructure/
│   ├── excel/                          # ✨ NEW MODULE
│   │   ├── __init__.py
│   │   ├── excel_processor.py          # Parse Excel files, detect schema
│   │   ├── data_profiler.py            # Generate statistics, insights
│   │   └── sheet_manager.py            # Multi-sheet handling
│   │
│   ├── ai/
│   │   ├── pandas_code_generator.py    # ✨ NEW - NL to Pandas code
│   │   ├── code_validator.py           # ✨ NEW - Security validation
│   │   ├── code_executor.py            # ✨ NEW - Sandboxed execution
│   │   └── query_classifier.py         # ✨ NEW - Intent classification
│   │
│   ├── visualization/                  # ✨ NEW MODULE
│   │   ├── __init__.py
│   │   ├── chart_generator.py          # Auto-generate charts
│   │   └── chart_selector.py           # Heuristic chart selection
│   │
│   ├── export/                         # ✨ NEW MODULE
│   │   ├── __init__.py
│   │   ├── excel_exporter.py           # Export to Excel
│   │   ├── csv_exporter.py             # Export to CSV
│   │   └── image_exporter.py           # Export charts as PNG/PDF
│   │
│   └── database/models/
│       ├── excel_models.py             # ✨ NEW - Excel-specific models
│       └── chat_models.py              # MODIFY - Add excel_document_id
│
├── application/
│   ├── use_cases/
│   │   ├── process_excel_file.py       # ✨ NEW
│   │   ├── execute_excel_query.py      # ✨ NEW
│   │   └── generate_visualization.py   # ✨ NEW
│   │
│   └── dto/
│       └── excel_dto.py                # ✨ NEW
│
└── presentation/api/
    └── excel_router.py                 # ✨ NEW - All Excel endpoints

frontend/src/
├── pages/
│   ├── ExcelUploadPage.jsx             # ✨ NEW
│   ├── ExcelAnalysisPage.jsx           # ✨ NEW - Main analysis UI
│   └── ExcelDashboardPage.jsx          # ✨ NEW - BI dashboard
│
├── components/
│   └── excel/                          # ✨ NEW MODULE
│       ├── ExcelUploader.jsx           # Drag-drop upload
│       ├── SheetSelector.jsx           # Tab navigation
│       ├── DataGrid.jsx                # AG Grid wrapper
│       ├── QueryPanel.jsx              # Chat-style query input
│       ├── CodePreview.jsx             # Show generated code
│       ├── ResultDisplay.jsx           # Show query results
│       ├── ChartDisplay.jsx            # Plotly charts
│       ├── ExportButton.jsx            # Export dropdown
│       └── StatsPanel.jsx              # Summary statistics
│
└── services/
    └── excelService.js                 # ✨ NEW - Excel API calls
```

---

## 📅 Milestone Breakdown

### **MILESTONE 1: Excel Processing & Data Intelligence (Days 1-7)**

#### **Day 1: Environment Setup**
**Tasks:**
- [ ] Create `excel-data-analysis` branch
- [ ] Install backend dependencies (pandas, openpyxl, etc.)
- [ ] Install frontend dependencies (ag-grid, plotly)
- [ ] Create folder structure
- [ ] Update `.gitignore` for Excel files
- [ ] Create database migration for new models

**Deliverables:**
- ✅ All dependencies installed
- ✅ Branch created and pushed
- ✅ Folder structure ready

**Review Gate:** None (setup phase)

---

#### **Day 2-3: Excel Processing Backend**

**File: `backend/src/infrastructure/excel/excel_processor.py`**
```python
class ExcelProcessor:
    async def process_file(file_path: str) -> ExcelDocument
    async def get_sheet_data(doc_id: int, sheet: str) -> DataFrame
    async def get_schema(doc_id: int, sheet: str) -> Dict
```

**File: `backend/src/infrastructure/excel/data_profiler.py`**
```python
class DataProfiler:
    def generate_statistics(df: DataFrame) -> Dict
    def detect_data_types(df: DataFrame) -> Dict
    def identify_key_columns(df: DataFrame) -> List[str]
```

**Database Models:**
```python
class ExcelDocument(Base):
    id: int
    user_id: int
    filename: str
    sheets: List[str]  # JSON array
    row_count: int
    column_count: int
    file_path: str
    created_at: datetime

class ExcelSheet(Base):
    id: int
    excel_document_id: int
    sheet_name: str
    schema: Dict  # JSON: {col_name: {type, nullable, unique_count}}
    statistics: Dict  # JSON: summary stats
    preview_data: Dict  # JSON: first 100 rows
```

**Tasks:**
- [ ] Implement `ExcelProcessor.process_file()`
- [ ] Implement multi-sheet detection
- [ ] Implement schema detection (data types, nullability)
- [ ] Implement `DataProfiler.generate_statistics()`
- [ ] Create database models
- [ ] Write migration script
- [ ] Add unit tests (80%+ coverage)

**Deliverables:**
- ✅ Excel files can be parsed
- ✅ Multi-sheet support working
- ✅ Schema detection accurate
- ✅ Database models created

**Review Gate:** 
- ⚠️ **Security Review**: File upload validation, path traversal prevention
- ⚠️ **Performance Review**: Process 10MB Excel in < 10 seconds

---

#### **Day 4-5: Excel Upload API**

**File: `backend/src/presentation/api/excel_router.py`**
```python
@router.post("/excel/upload")
async def upload_excel_file(...)

@router.get("/excel/{doc_id}")
async def get_excel_document(...)

@router.get("/excel/{doc_id}/sheets")
async def list_sheets(...)

@router.get("/excel/{doc_id}/sheets/{sheet_name}/preview")
async def get_sheet_preview(...)

@router.get("/excel/{doc_id}/sheets/{sheet_name}/schema")
async def get_sheet_schema(...)

@router.get("/excel/{doc_id}/sheets/{sheet_name}/stats")
async def get_sheet_statistics(...)
```

**Tasks:**
- [ ] Create `excel_router.py` with all endpoints
- [ ] Implement file upload with validation (max 50MB)
- [ ] Implement sheet listing endpoint
- [ ] Implement preview endpoint (paginated, 100 rows)
- [ ] Implement schema endpoint
- [ ] Add authentication middleware
- [ ] Add error handling
- [ ] Write integration tests

**Deliverables:**
- ✅ All API endpoints working
- ✅ Postman collection for testing
- ✅ OpenAPI documentation updated

**Review Gate:** 
- ⚠️ **Security Review**: Authentication, file size limits, MIME type validation

---

#### **Day 6-7: Excel Preview Frontend**

**File: `frontend/src/pages/ExcelUploadPage.jsx`**
- Drag-and-drop file uploader
- File validation (client-side)
- Upload progress bar
- Redirect to analysis page after upload

**File: `frontend/src/pages/ExcelAnalysisPage.jsx`**
- Sheet selector tabs
- Data grid with AG Grid
- Summary statistics panel
- Column type indicators

**File: `frontend/src/components/excel/DataGrid.jsx`**
- Wrap AG Grid with custom styling
- Column resizing, sorting, filtering
- Pagination (50 rows per page)
- Dark mode support

**Tasks:**
- [ ] Create `ExcelUploadPage.jsx`
- [ ] Implement drag-and-drop with react-dropzone
- [ ] Create `ExcelAnalysisPage.jsx`
- [ ] Implement sheet selector tabs
- [ ] Integrate AG Grid for data display
- [ ] Add summary statistics panel
- [ ] Add loading states and error handling
- [ ] Responsive design (mobile-friendly)

**Deliverables:**
- ✅ Upload page functional
- ✅ Preview page showing data correctly
- ✅ Multi-sheet navigation working

**Review Gate:**
- ⚠️ **Performance Review**: Grid renders 10k rows smoothly
- ⚠️ **Code Quality Review**: Component structure, reusability

---

### **MILESTONE 2: Natural Language Query & Code Generation (Days 8-14)**

#### **Day 8-9: Query Classification**

**File: `backend/src/infrastructure/ai/query_classifier.py`**
```python
class QueryClassifier:
    INTENTS = [
        "AGGREGATION",     # sum, average, count
        "FILTERING",       # filter by condition
        "GROUPING",        # group by column
        "SORTING",         # sort by column
        "TOP_N",          # top/bottom N records
        "CALCULATION",     # mathematical operations
        "PIVOT",          # pivot table
        "CORRELATION"     # correlation analysis
    ]
    
    async def classify_query(query: str, schema: Dict) -> Intent
    async def extract_entities(query: str, schema: Dict) -> Entities
```

**Tasks:**
- [ ] Implement intent classification using Claude
- [ ] Extract entities (columns, values, operations)
- [ ] Create prompt templates for classification
- [ ] Handle ambiguous queries
- [ ] Add query validation
- [ ] Write unit tests

**Deliverables:**
- ✅ 90%+ accuracy in intent classification
- ✅ Entity extraction working

---

#### **Day 10-11: Pandas Code Generation**

**File: `backend/src/infrastructure/ai/pandas_code_generator.py`**
```python
class PandasCodeGenerator:
    async def generate_code(query: str, schema: Dict, intent: Intent) -> str
    async def optimize_code(code: str) -> str
    def _create_prompt(query: str, schema: Dict) -> str
```

**Prompt Template:**
```
You are an expert Python data analyst. Generate pandas code to answer this question.

Dataset Schema:
{schema}

User Question: {query}

Rules:
1. Use variable 'df' for the input DataFrame
2. Store final result in variable 'result'
3. Only use: pandas, numpy, datetime
4. No file I/O, no system calls
5. Handle missing values gracefully
6. Return result in analyzable format (DataFrame, Series, or scalar)

Generate ONLY the Python code, no explanations.
```

**Tasks:**
- [ ] Implement code generation with Claude
- [ ] Create comprehensive prompt templates
- [ ] Handle different query intents
- [ ] Add code optimization logic
- [ ] Test with 50+ sample queries
- [ ] Document supported query patterns

**Deliverables:**
- ✅ Code generation working for all intents
- ✅ 85%+ accuracy on test queries

**Review Gate:**
- ⚠️ **AI Integration Review**: Code quality, accuracy

---

#### **Day 12: Code Validation & Sandboxing**

**File: `backend/src/infrastructure/ai/code_validator.py`**
```python
class CodeValidator:
    ALLOWED_IMPORTS = ['pandas', 'numpy', 'datetime']
    FORBIDDEN_CALLS = ['eval', 'exec', 'compile', '__import__']
    
    def validate_syntax(code: str) -> bool
    def validate_security(code: str) -> bool
    def check_imports(code: str) -> List[str]
    def detect_dangerous_operations(code: str) -> List[str]
```

**File: `backend/src/infrastructure/ai/code_executor.py`**
```python
class CodeExecutor:
    def __init__(self, timeout: int = 5, memory_limit: int = 512):
        pass
    
    async def execute(code: str, df: pd.DataFrame) -> ExecutionResult
    def _create_safe_globals(df: pd.DataFrame) -> Dict
    def _enforce_timeout(func, timeout: int)
```

**Security Measures:**
- ✅ AST parsing to detect forbidden operations
- ✅ Whitelist only pandas, numpy, datetime
- ✅ RestrictedPython for safe execution
- ✅ CPU timeout (5 seconds)
- ✅ Memory limit (512 MB)
- ✅ No file I/O operations
- ✅ No network operations

**Tasks:**
- [ ] Implement AST-based code validation
- [ ] Implement sandboxed execution
- [ ] Add resource limits (timeout, memory)
- [ ] Test with malicious code samples
- [ ] Add comprehensive error messages
- [ ] Write security tests

**Deliverables:**
- ✅ Code validation prevents all dangerous operations
- ✅ Sandbox prevents system access

**Review Gate:**
- ⚠️ **Security Review**: CRITICAL - Must pass penetration tests

---

#### **Day 13-14: Query Interface Frontend**

**File: `frontend/src/components/excel/QueryPanel.jsx`**
- Chat-style input box
- Example query buttons
- Query suggestions based on schema
- Loading state
- Code preview (collapsible)
- Error handling with retry

**File: `frontend/src/components/excel/ResultDisplay.jsx`**
- Display query results (table/scalar/series)
- Format numbers, dates appropriately
- Download result button

**Tasks:**
- [ ] Create `QueryPanel.jsx` component
- [ ] Implement query input with suggestions
- [ ] Add example queries (context-aware)
- [ ] Create `CodePreview.jsx` for generated code
- [ ] Create `ResultDisplay.jsx`
- [ ] Add error handling UI
- [ ] Integrate with backend API
- [ ] Add loading animations

**Deliverables:**
- ✅ Query interface fully functional
- ✅ Results displayed correctly
- ✅ Good UX with loading states

**Review Gate:**
- ⚠️ **Performance Review**: Query response < 5 seconds

---

### **MILESTONE 3: Visualization & Business Intelligence (Days 15-21)**

#### **Day 15-16: Chart Generation**

**File: `backend/src/infrastructure/visualization/chart_selector.py`**
```python
class ChartSelector:
    def select_chart_type(df: DataFrame, query: str) -> ChartType
    
    # Heuristics:
    # - 1 numeric column → histogram
    # - 1 categorical + 1 numeric → bar chart
    # - 2 numeric columns → scatter plot
    # - Time series → line chart
    # - Multiple categories → grouped bar / stacked bar
```

**File: `backend/src/infrastructure/visualization/chart_generator.py`**
```python
class ChartGenerator:
    async def generate_chart(df: DataFrame, chart_type: str) -> PlotlyJSON
    async def generate_interactive_chart(df: DataFrame) -> PlotlyJSON
    def _optimize_chart_size(fig: go.Figure) -> go.Figure
```

**Supported Chart Types:**
- Bar chart (horizontal/vertical)
- Line chart
- Scatter plot
- Pie chart
- Histogram
- Box plot
- Heatmap
- Time series

**Tasks:**
- [ ] Implement chart type selection heuristics
- [ ] Implement Plotly chart generation for all types
- [ ] Add chart customization (colors, labels, title)
- [ ] Optimize chart size and performance
- [ ] Add chart export to PNG/PDF
- [ ] Write unit tests

**Deliverables:**
- ✅ All chart types working
- ✅ Automatic chart selection accurate

---

#### **Day 17-18: Chart Display Frontend**

**File: `frontend/src/components/excel/ChartDisplay.jsx`**
```jsx
<ChartDisplay 
  plotlyJson={chartData}
  onExport={(format) => handleExport(format)}
  interactive={true}
/>
```

**Features:**
- Interactive Plotly charts (zoom, pan, hover)
- Chart type selector dropdown
- Download button (PNG, SVG, PDF)
- Full-screen mode
- Dark mode support

**Tasks:**
- [ ] Integrate react-plotly.js
- [ ] Create `ChartDisplay.jsx`
- [ ] Add interactivity controls
- [ ] Implement chart export
- [ ] Add responsive sizing
- [ ] Add loading skeleton

**Deliverables:**
- ✅ Charts render correctly
- ✅ Interactivity working
- ✅ Export functional

**Review Gate:**
- ⚠️ **Performance Review**: Chart renders in < 3 seconds

---

#### **Day 19: Export Functionality**

**File: `backend/src/infrastructure/export/excel_exporter.py`**
```python
class ExcelExporter:
    async def export_result(df: DataFrame, filename: str) -> bytes
    def format_excel(writer: ExcelWriter, df: DataFrame)
```

**File: `backend/src/infrastructure/export/csv_exporter.py`**
```python
class CSVExporter:
    async def export_result(df: DataFrame) -> bytes
```

**File: `backend/src/infrastructure/export/image_exporter.py`**
```python
class ImageExporter:
    async def export_chart_png(fig: go.Figure) -> bytes
    async def export_chart_pdf(fig: go.Figure) -> bytes
```

**API Endpoints:**
```python
@router.post("/excel/{doc_id}/export")
async def export_result(
    doc_id: int,
    format: Literal["xlsx", "csv", "png", "pdf"],
    data: Dict
) -> FileResponse
```

**Tasks:**
- [ ] Implement Excel export with formatting
- [ ] Implement CSV export
- [ ] Implement PNG export (chart)
- [ ] Implement PDF export (chart + data)
- [ ] Add export API endpoint
- [ ] Create frontend export button
- [ ] Test all export formats

**Deliverables:**
- ✅ All export formats working
- ✅ Files downloadable from frontend

---

#### **Day 20: BI Dashboard**

**File: `frontend/src/pages/ExcelDashboardPage.jsx`**
```jsx
<ExcelDashboard>
  <MetricsPanel stats={stats} />
  <ChartsGrid>
    <ChartDisplay chart={chart1} />
    <ChartDisplay chart={chart2} />
  </ChartsGrid>
  <RecentQueries queries={history} />
</ExcelDashboard>
```

**Features:**
- Key metrics cards (row count, column count, null count)
- Multiple charts in grid layout
- Recent queries history
- Quick filters
- Refresh button

**Tasks:**
- [ ] Create `ExcelDashboardPage.jsx`
- [ ] Design grid layout
- [ ] Add metrics cards
- [ ] Integrate multiple charts
- [ ] Add query history
- [ ] Make responsive

**Deliverables:**
- ✅ Dashboard page functional
- ✅ Multiple charts displayed

---

#### **Day 21: Testing & Documentation**

**Testing Checklist:**
- [ ] Unit tests (90%+ coverage)
- [ ] Integration tests (API endpoints)
- [ ] E2E tests (Playwright)
- [ ] Security tests (penetration testing)
- [ ] Performance tests (load testing)
- [ ] Browser compatibility (Chrome, Firefox, Safari)

**Documentation:**
- [ ] API documentation (OpenAPI/Swagger)
- [ ] User guide (how to upload, query, export)
- [ ] Developer guide (architecture, setup)
- [ ] Security documentation (sandboxing details)
- [ ] Query examples library

**Final Review:**
- [ ] Code review (peer review)
- [ ] Security audit
- [ ] Performance profiling
- [ ] Accessibility audit (WCAG 2.1)

---

## 🎯 Success Criteria

### **Performance Benchmarks:**
| Metric | Target | Critical |
|--------|--------|----------|
| Excel Processing (10MB) | < 10s | < 15s |
| Query Processing | < 5s | < 8s |
| Chart Generation | < 3s | < 5s |
| Export Generation | < 5s | < 8s |

### **Quality Metrics:**
| Metric | Target | Critical |
|--------|--------|----------|
| Code Coverage | 90%+ | 80%+ |
| Code Generation Accuracy | 90%+ | 85%+ |
| Security Score | 9.5/10 | 9.0/10 |
| Performance Score | 9.0/10 | 8.5/10 |

### **Review Gates:**
- ✅ **M1**: Security (8.5/10), Performance (8.5/10)
- ✅ **M2**: AI Integration (9.0/10), Security (9.5/10)
- ✅ **M3**: Architecture (8.5/10), Performance (9.0/10)

---

## 🚨 Risk Management

### **High Risk Areas:**
1. **Code Execution Security** 🔴
   - **Risk**: Malicious code injection
   - **Mitigation**: Multi-layer validation, sandboxing, timeouts
   
2. **AI Code Accuracy** 🟡
   - **Risk**: Generated code produces wrong results
   - **Mitigation**: Extensive testing, code review, user validation

3. **Performance at Scale** 🟡
   - **Risk**: Large Excel files (100MB+) crash server
   - **Mitigation**: File size limits, chunked processing, streaming

4. **Memory Leaks** 🟡
   - **Risk**: Pandas DataFrames not garbage collected
   - **Mitigation**: Explicit cleanup, memory profiling

---

## 📊 Progress Tracking

### **Completed:**
- [x] Implementation plan created
- [ ] Environment setup
- [ ] Dependencies installed

### **In Progress:**
- [ ] None

### **Blocked:**
- [ ] None

---

## 🔗 Related Documents

- [Project Requirements](./PROJECT_REQUIREMENTS.md) - Original project spec
- [API Documentation](./API_DOCUMENTATION.md) - API endpoint details
- [Security Audit](./SECURITY_AUDIT.md) - Security review results
- [Test Coverage Report](./COVERAGE_REPORT.md) - Testing metrics

---

## 📝 Notes

- **Branch**: All work must be on `excel-data-analysis` branch
- **Commits**: Use conventional commits (feat:, fix:, docs:)
- **Reviews**: Request review before merging to main
- **Deployment**: Staging environment testing required

---

**Last Updated**: October 6, 2025  
**Status**: ✅ PLANNING COMPLETE - READY TO START IMPLEMENTATION
