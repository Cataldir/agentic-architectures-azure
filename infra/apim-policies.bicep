param apimName string
param mcpApiName string
param llmApiName string
resource apim 'Microsoft.ApiManagement/service@2024-05-01' existing = { name: apimName }
resource mcp 'Microsoft.ApiManagement/service/apis@2024-05-01' existing = { parent: apim, name: mcpApiName }
resource llm 'Microsoft.ApiManagement/service/apis@2024-05-01' existing = { parent: apim, name: llmApiName }
resource tools 'Microsoft.ApiManagement/service/apis/policies@2024-05-01' = {
  parent: mcp
  name: 'policy'
  properties: { format: 'rawxml', value: loadTextContent('../policies/mcp.xml') }
}
resource inference 'Microsoft.ApiManagement/service/apis/policies@2024-05-01' = {
  parent: llm
  name: 'policy'
  properties: { format: 'rawxml', value: loadTextContent('../policies/llm-cache.xml') }
}
