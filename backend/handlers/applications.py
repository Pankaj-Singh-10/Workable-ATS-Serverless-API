import os
import json
import requests

def get_applications(event, context):
    """
    GET /applications?job_id=... - List applications for a given job
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
        
        # Get job_id from query parameters
        query_params = event.get('queryStringParameters') or {}
        job_id = query_params.get('job_id')
        
        if not job_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'job_id parameter is required'})
            }
        
        # Workable API endpoint for job candidates
        url = f"https://{subdomain}.workable.com/spi/v3/jobs/{job_id}/candidates"
        print(f"Calling Workable URL: {url}")  # Debug log
        
        # Headers for Workable API
        api_headers = {
            'Authorization': f'Bearer {api_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Make request to Workable API
        response = requests.get(
            url,
            headers=api_headers,
            params={'limit': 100},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")  # Debug log
        print(f"Response body: {response.text}")  # Debug log
        
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
        
        # Transform to your required format
        applications = []
        
        # Check if 'candidates' exists and is a list
        candidates_list = data.get('candidates', [])
        
        for candidate in candidates_list:
            # Make sure candidate is a dictionary
            if not isinstance(candidate, dict):
                print(f"Skipping non-dictionary candidate: {candidate}")
                continue
            
            # Get stage information safely
            stage_data = candidate.get('stage', {})
            
            # Handle case where stage might be a string or dict
            if isinstance(stage_data, dict):
                stage_slug = stage_data.get('slug', 'applied')
            else:
                stage_slug = str(stage_data) if stage_data else 'applied'
            
            # Map Workable stage to your status format
            stage_map = {
                'sourced': 'APPLIED',
                'applied': 'APPLIED',
                'phone_screen': 'SCREENING',
                'interview': 'SCREENING',
                'assessment': 'SCREENING',
                'offer': 'SCREENING',
                'hired': 'HIRED',
                'rejected': 'REJECTED',
                'disqualified': 'REJECTED'
            }
            
            applications.append({
                'id': candidate.get('id', ''),
                'candidate_name': candidate.get('name', 'Unknown'),
                'email': candidate.get('email', ''),
                'status': stage_map.get(stage_slug, 'APPLIED')
            })
        
        # Handle pagination
        paging = data.get('paging', {})
        pagination = {
            'total': paging.get('total_count', len(applications)),
            'has_next': paging.get('next') is not None
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'applications': applications,
                'pagination': pagination
            })
        }
        
    except Exception as e:
        print(f"Error in get_applications: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': str(e)
            })
        }
    
