Generowanie analizy 
```
curl --location 'localhost:8000/api/stock-analysis/run-api' \
--header 'Content-Type: application/json' \
--header 'Cookie: XSRF-TOKEN=eyJpdiI6IjRUVExTSStuVGNjdi9vc1VQWkxWYXc9PSIsInZhbHVlIjoiUjhqcHI1T0RMTjFVcTNxdTI4c2JMMGpVcE1odWNrd2diR21KTnlvNmV6K1g4SitFb1lXUWd1MnBWSDFzWThJYWFtN2FkQzA2RzMzMjUwekMzS05pbWVUZzNLWVhjRlpnbFRRbzJqVnVmdi9VZm9hZnB0YVZXcUNIVFd1N3RSNWMiLCJtYWMiOiJhM2YzZTZhMjM0YmEyZGIwOTBlOGIyODQyMTg3ODc1NDg0ZWUwZWVlNTYwMTViYTEyY2IxMmU5MjQ4MzRjMjk3IiwidGFnIjoiIn0%3D; laravel_session=eyJpdiI6ImxqQy9qcHgxZnFzQmN2VDFlSGJaQWc9PSIsInZhbHVlIjoiT29UaWtnYmxXS2Q0SHZZcjdETW00SWhkQjlBOEM3V0U0TnNWTUp1VkI4bWJsUlNJU2dGaVB4bHluNWUrU2NTanh4K1laK1plMFFQcXpDZE5YMVlIMTRaaG5XOXJUL0NzTmo1RFU3R2prRnhOQ3NSakZ5WURScmk4bmYyRFV4aWEiLCJtYWMiOiIxOWEyNWExYzFlMDk0NDBhOWQ2YjRlNjFlZjJlN2U3YjQ2OTY4NDliNDAzNTMzMzMxMjkyNzVjOTA0Njg1MmExIiwidGFnIjoiIn0%3D' \
--data '{
    "ticker": "BTC-USD",
    "trends": "bitcoin",
    "start_date": "2017-01-01", 
    "test_size_pct": 0.15,
    "forecast_days": 20
}'
```
