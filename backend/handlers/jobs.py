import os
import json
import requests

def get_jobs(event, context):
    """
    GET /jobs - Return list of jobs from Workable
    """
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }
    
    try:
        # Get credentials
        subdomain = os.environ.get('WORKABLE_SUBDOMAIN')
        api_token = os.environ.get('WORKABLE_API_TOKEN')
        
        if not subdomain or not api_token:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': 'Missing Workable credentials'})
            }
        
        # Get pagination params
        query_params = event.get('queryStringParameters') or {}
        page = query_params.get('page', '1')
        limit = query_params.get('limit', '50')  # Workable default is 50 [citation:3]
        
        # Workable API request [citation:6]
        url = f"https://{subdomain}.workable.com/spi/v3/jobs"
        
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {api_token}'},
            params={'page': page, 'limit': limit},
            timeout=30
        )
        
        # Handle Workable API errors
        if response.status_code != 200:
            return {
                'statusCode': response.status_code,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Workable API error',
                    'message': f"Status {response.status_code}"
                })
            }
        
        data = response.json()
        
        # Transform to our standard format [citation:3]
        jobs = []
        for job in data.get('jobs', []):
            # Map Workable state to our status [citation:6]
            status_map = {
                'published': 'OPEN',
                'closed': 'CLOSED',
                'draft': 'DRAFT',
                'archived': 'CLOSED'
            }
            
            # Get location string
            location = job.get('location', {})
            if isinstance(location, dict):
                location_str = location.get('location_str', 'Remote')
            else:
                location_str = str(location)
            
            jobs.append({
                'id': job.get('shortcode') or job.get('id'),
                'title': job.get('title'),
                'location': location_str,
                'status': status_map.get(job.get('state', 'draft'), 'DRAFT'),
                'external_url': job.get('application_url') or job.get('url')
            })
        
        # Handle pagination [citation:3][citation:7]
        pagination = {
            'current_page': int(page),
            'total_pages': data.get('paging', {}).get('total_pages', 1),
            'total_count': data.get('paging', {}).get('total_count', len(jobs)),
            'has_next': data.get('paging', {}).get('next') is not None,
            'next_url': data.get('paging', {}).get('next')
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'jobs': jobs,
                'pagination': pagination
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
    
