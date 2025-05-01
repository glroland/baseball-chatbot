from mcp.server.fastmcp import FastMCP
import uvicorn

mcp = FastMCP("Calculator")

@mcp.tool()
def calculator(x: float, y: float, operation: str) -> dict:
    """Simple calculator tool that performs basic math operations.

    :param x: First number to perform operation on
    :param y: Second number to perform operation on
    :param operation: Mathematical operation to perform ('add', 'subtract', 'multiply', 'divide')
    :returns: Dictionary containing success status and result or error message
    """
    try:
        if operation == "add":
            result = float(x) + float(y)
        elif operation == "subtract":
            result = float(x) - float(y)
        elif operation == "multiply":
            result = float(x) * float(y)
        elif operation == "divide":
            if float(y) == 0:
                return {"success": False, "error": "Cannot divide by zero"}
            result = float(x) / float(y)
        else:
            return {"success": False, "error": "Invalid operation"}

        return {"success": True, "result": result}
    except Exception as e:
        print(f"Calculator error: {str(e)}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

if __name__ == "__main__":
    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=8080)
