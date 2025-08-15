#!/usr/bin/env python3
"""
MCP Data Analysis Server
A Model Context Protocol server providing data analysis tools
"""

from mcp.server import Server, logger
from mcp.server.models import ServerInfo, ListResourcesResponse, ReadResourceResponse
from mcp.types import ServerCapabilities, Tool, TextContent, Resource
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3
import os


class DataAnalysisRequest(BaseModel):
    """Request structure for data analysis"""
    operation: str = Field(description="Type of analysis: 'describe', 'aggregate', 'filter', 'transform'")
    data: List[Dict[str, Any]] = Field(description="Data to analyze")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters")


class QueryDatabaseRequest(BaseModel):
    """Request structure for database queries"""
    query: str = Field(description="SQL query to execute")
    database: Optional[str] = Field(default="memory", description="Database name or ':memory:' for in-memory")


class StatisticsResult(BaseModel):
    """Result structure for statistical analysis"""
    mean: Optional[float] = None
    median: Optional[float] = None
    std_dev: Optional[float] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    count: int = 0
    unique_count: Optional[int] = None


# Initialize MCP server
app = Server("data-analysis-server")


def analyze_data(request: DataAnalysisRequest) -> Dict[str, Any]:
    """
    Perform data analysis operations
    """
    df = pd.DataFrame(request.data)
    
    if request.operation == "describe":
        # Statistical description
        desc = df.describe().to_dict()
        return {"statistics": desc}
    
    elif request.operation == "aggregate":
        params = request.params or {}
        group_by = params.get("group_by", [])
        agg_func = params.get("agg_func", "mean")
        
        if group_by:
            result = df.groupby(group_by).agg(agg_func)
            return {"aggregated": result.to_dict()}
        else:
            return {"error": "group_by parameter required for aggregation"}
    
    elif request.operation == "filter":
        params = request.params or {}
        conditions = params.get("conditions", {})
        
        for col, condition in conditions.items():
            if col in df.columns:
                if isinstance(condition, dict):
                    op = condition.get("operator", "==")
                    val = condition.get("value")
                    
                    if op == "==":
                        df = df[df[col] == val]
                    elif op == ">":
                        df = df[df[col] > val]
                    elif op == "<":
                        df = df[df[col] < val]
                    elif op == ">=":
                        df = df[df[col] >= val]
                    elif op == "<=":
                        df = df[df[col] <= val]
                    elif op == "!=":
                        df = df[df[col] != val]
        
        return {"filtered": df.to_dict(orient="records")}
    
    elif request.operation == "transform":
        params = request.params or {}
        transformations = params.get("transformations", {})
        
        for col, transform in transformations.items():
            if transform == "normalize":
                if col in df.columns and df[col].dtype in [np.float64, np.int64]:
                    df[col] = (df[col] - df[col].mean()) / df[col].std()
            elif transform == "log":
                if col in df.columns and df[col].dtype in [np.float64, np.int64]:
                    df[col] = np.log(df[col].replace(0, np.nan))
        
        return {"transformed": df.to_dict(orient="records")}
    
    else:
        return {"error": f"Unknown operation: {request.operation}"}


def query_database(request: QueryDatabaseRequest) -> Dict[str, Any]:
    """
    Execute SQL queries on database
    """
    try:
        # Connect to database (in-memory by default)
        if request.database == "memory" or request.database == ":memory:":
            conn = sqlite3.connect(":memory:")
        else:
            db_path = f"/tmp/{request.database}.db"
            conn = sqlite3.connect(db_path)
        
        cursor = conn.cursor()
        
        # Execute query
        cursor.execute(request.query)
        
        # Check if it's a SELECT query
        if request.query.strip().upper().startswith("SELECT"):
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            conn.close()
            return {"results": result, "row_count": len(result)}
        else:
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            return {"affected_rows": affected, "success": True}
    
    except Exception as e:
        return {"error": str(e)}


def calculate_statistics(data: List[float]) -> StatisticsResult:
    """
    Calculate comprehensive statistics for numerical data
    """
    if not data:
        return StatisticsResult(count=0)
    
    arr = np.array(data)
    return StatisticsResult(
        mean=float(np.mean(arr)),
        median=float(np.median(arr)),
        std_dev=float(np.std(arr)),
        min_val=float(np.min(arr)),
        max_val=float(np.max(arr)),
        count=len(arr),
        unique_count=len(np.unique(arr))
    )


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="analyze_data",
            description="Perform data analysis operations (describe, aggregate, filter, transform)",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["describe", "aggregate", "filter", "transform"],
                        "description": "Type of analysis to perform"
                    },
                    "data": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Data to analyze as array of objects"
                    },
                    "params": {
                        "type": "object",
                        "description": "Additional parameters for the operation"
                    }
                },
                "required": ["operation", "data"]
            }
        ),
        Tool(
            name="query_database",
            description="Execute SQL queries on a database",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute"
                    },
                    "database": {
                        "type": "string",
                        "description": "Database name or ':memory:' for in-memory",
                        "default": "memory"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="calculate_statistics",
            description="Calculate comprehensive statistics for numerical data",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Array of numerical values"
                    }
                },
                "required": ["data"]
            }
        ),
        Tool(
            name="generate_sample_data",
            description="Generate sample datasets for testing",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_type": {
                        "type": "string",
                        "enum": ["sales", "users", "timeseries", "random"],
                        "description": "Type of sample data to generate"
                    },
                    "rows": {
                        "type": "integer",
                        "description": "Number of rows to generate",
                        "default": 100
                    }
                },
                "required": ["dataset_type"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        if name == "analyze_data":
            request = DataAnalysisRequest(**arguments)
            result = analyze_data(request)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "query_database":
            request = QueryDatabaseRequest(**arguments)
            result = query_database(request)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "calculate_statistics":
            data = arguments.get("data", [])
            stats = calculate_statistics(data)
            return [TextContent(type="text", text=json.dumps(stats.dict(), indent=2))]
        
        elif name == "generate_sample_data":
            dataset_type = arguments.get("dataset_type")
            rows = arguments.get("rows", 100)
            
            if dataset_type == "sales":
                data = []
                for i in range(rows):
                    data.append({
                        "order_id": f"ORD-{i:05d}",
                        "date": f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                        "amount": round(np.random.uniform(10, 1000), 2),
                        "quantity": np.random.randint(1, 20),
                        "product": np.random.choice(["Widget A", "Widget B", "Widget C"]),
                        "customer_id": f"CUST-{np.random.randint(1, 50):03d}"
                    })
            elif dataset_type == "users":
                data = []
                for i in range(rows):
                    data.append({
                        "user_id": f"USER-{i:05d}",
                        "name": f"User_{i}",
                        "age": np.random.randint(18, 80),
                        "email": f"user{i}@example.com",
                        "registered": f"2024-{np.random.randint(1, 12):02d}-{np.random.randint(1, 28):02d}",
                        "active": np.random.choice([True, False])
                    })
            elif dataset_type == "timeseries":
                data = []
                base_value = 100
                for i in range(rows):
                    base_value += np.random.uniform(-5, 5)
                    data.append({
                        "timestamp": f"2024-01-01T{i:02d}:00:00Z",
                        "value": round(base_value, 2),
                        "metric": "temperature"
                    })
            else:  # random
                data = []
                for i in range(rows):
                    data.append({
                        "id": i,
                        "value1": round(np.random.uniform(0, 100), 2),
                        "value2": round(np.random.uniform(0, 100), 2),
                        "category": np.random.choice(["A", "B", "C", "D"])
                    })
            
            return [TextContent(type="text", text=json.dumps({"data": data, "count": len(data)}, indent=2))]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@app.get_server_info()
async def get_server_info() -> ServerInfo:
    """Get server information"""
    return ServerInfo(
        name="Data Analysis MCP Server",
        version="1.0.0",
        protocolVersion="1.0",
        capabilities=ServerCapabilities(
            tools=True,
            resources=True
        )
    )


@app.list_resources()
async def list_resources() -> ListResourcesResponse:
    """List available resources"""
    return ListResourcesResponse(
        resources=[
            Resource(
                uri="data://sample/sales",
                name="Sample Sales Data",
                description="Sample sales dataset for testing",
                mimeType="application/json"
            ),
            Resource(
                uri="data://sample/users",
                name="Sample Users Data",
                description="Sample user dataset for testing",
                mimeType="application/json"
            )
        ]
    )


@app.read_resource()
async def read_resource(uri: str) -> ReadResourceResponse:
    """Read a resource"""
    if uri == "data://sample/sales":
        data = [
            {"order_id": "ORD-001", "amount": 150.00, "product": "Widget A"},
            {"order_id": "ORD-002", "amount": 250.00, "product": "Widget B"},
            {"order_id": "ORD-003", "amount": 75.00, "product": "Widget C"}
        ]
        return ReadResourceResponse(
            contents=[TextContent(type="text", text=json.dumps(data, indent=2))]
        )
    elif uri == "data://sample/users":
        data = [
            {"user_id": "USER-001", "name": "Alice", "age": 30},
            {"user_id": "USER-002", "name": "Bob", "age": 25},
            {"user_id": "USER-003", "name": "Charlie", "age": 35}
        ]
        return ReadResourceResponse(
            contents=[TextContent(type="text", text=json.dumps(data, indent=2))]
        )
    else:
        return ReadResourceResponse(
            contents=[TextContent(type="text", text="Resource not found")]
        )


async def main():
    """Main entry point"""
    logger.info("Starting Data Analysis MCP Server")
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.get_server_info(),
            raise_exceptions=True
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())