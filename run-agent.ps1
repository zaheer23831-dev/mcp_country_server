# Set environment variables
$env:DEEPSEEK_API_KEY = "sk-f39eb41ffa374f55ab7bd12d1c53225c"
$env:MCP_BASE_URL     = "http://localhost:3000"
$env:MCP_API_KEY      = "dev-key-123"
$env:SERVICE_PORT     = "5050"

# Run MCP server (if not already running)
Write-Host ">>> Starting MCP server on port 3000..."
Start-Process powershell -ArgumentList "python server.py" -NoNewWindow

Start-Sleep -Seconds 3

# Run DeepSeek agent service
Write-Host ">>> Starting DeepSeek Agent service on port $env:SERVICE_PORT ..."
python deepseek_agent_service.py
