# -*- coding: utf-8 -*-
"""
Enhanced Metrics Logging Middleware
Automatically tracks API calls, performance, and system health
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.metrics import metrics_collector
from ..core.performance_monitor import performance_monitor

class MetricsMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware to log API calls, performance metrics, and system health"""
    
    async def dispatch(self, request: Request, call_next):
        # Record start time
        start_time = time.time()
        
        # Get request info
        method = request.method
        path = str(request.url.path)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            process_time_ms = process_time * 1000
            
            # Log the API call
            metrics_collector.log_api_call(endpoint=path, method=method)
            
            # Log response time for performance monitoring
            performance_monitor.log_response_time(process_time_ms)
            
            # Estimate data processed based on response size and processing time
            if hasattr(response, 'body'):
                try:
                    # Estimate data size (response + some processing overhead)
                    estimated_size_mb = len(getattr(response, 'body', b'')) / (1024 * 1024)
                    if estimated_size_mb > 0:
                        metrics_collector.log_data_processed(estimated_size_mb)
                except:
                    # Fallback: estimate based on processing time
                    estimated_size_mb = process_time * 0.01  # 10KB per second estimate
                    metrics_collector.log_data_processed(estimated_size_mb)
            
            # Log database operations based on endpoint patterns
            if any(db_endpoint in path for db_endpoint in ['/employees', '/users', '/leave', '/attendance']):
                if method == 'GET':
                    metrics_collector.log_database_operation('query')
                elif method == 'POST':
                    metrics_collector.log_database_operation('insert')
                elif method in ['PUT', 'PATCH']:
                    metrics_collector.log_database_operation('update')
                elif method == 'DELETE':
                    metrics_collector.log_database_operation('delete')
            
            # Add enhanced metrics headers to response
            response.headers["X-Process-Time"] = str(process_time_ms)
            response.headers["X-API-Calls-Today"] = str(metrics_collector.get_api_calls_today())
            response.headers["X-Data-Processed-MB"] = str(round(metrics_collector.get_data_processed_today(), 2))
            
            return response
            
        except Exception as e:
            # Log error for performance monitoring
            performance_monitor.log_error("request_processing")
            
            # Calculate processing time even for errors
            process_time = time.time() - start_time
            process_time_ms = process_time * 1000
            performance_monitor.log_response_time(process_time_ms)
            
            # Re-raise the exception
            raise e