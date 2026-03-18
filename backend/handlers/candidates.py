import os
import json
import requests

def create_candidate(event, context):
    """
    POST /candidates - Create a candidate in Workable and attach to job
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
            print("ERROR: Missing Workable credentials")
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': 'Missing Workable credentials'})
            }
        
        # Parse candidate data
        if not event.get('body'):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Request body required'})
            }
        
        candidate = json.loads(event['body'])
        print(f"Received candidate data: {candidate}")  # Debug log
        
        # Validate required fields
        required = ['name', 'email', 'job_id']
        missing = [f for f in required if f not in candidate]
        if missing:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': f"Missing fields: {missing}"
                })
            }
        
        # Validate email format
        if '@' not in candidate['email']:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Invalid email format'
                })
            }
        
        # Validate URL if provided
        if candidate.get('resume_url'):
            # Check if URL is valid
            if not candidate['resume_url'].startswith(('http://', 'https://')):
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'error': 'Invalid URL format',
                        'message': 'Resume URL must start with http:// or https://'
                    })
                }
        
        # CORRECT Workable API endpoint for creating candidates for a specific job
        # The job_id goes in the URL path
        url = f"https://{subdomain}.workable.com/spi/v3/jobs/{candidate['job_id']}/candidates"
        print(f"Calling Workable URL: {url}")  # Debug log
        
        # Headers for Workable API
        api_headers = {
            'Authorization': f'Bearer {api_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Split name into first and last name
        name_parts = candidate['name'].split(' ')
        firstname = name_parts[0]
        lastname = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        
        # Candidate data in Workable format (without job_id since it's in URL)
        workable_data = {
            'name': candidate['name'],
            'firstname': firstname,
            'lastname': lastname,
            'email': candidate['email'],
            'sourced': True,  # Mark as applied via external source
            'stage': 'applied'  # Use lowercase as per Workable API
        }
        
        # Add optional fields if present
        if candidate.get('phone'):
            workable_data['phone'] = candidate['phone']
        
        if candidate.get('resume_url'):
            workable_data['resume_url'] = candidate['resume_url']
        
        print(f"Workable request data: {workable_data}")  # Debug log
        
        # Make request to Workable API
        response = requests.post(
            url,
            headers=api_headers,
            json=workable_data,
            timeout=30
        )
        
        print(f"Workable response status: {response.status_code}")  # Debug log
        print(f"Workable response body: {response.text}")  # Debug log
        
        # Handle rate limiting (10 requests per 10 seconds)
        if response.status_code == 429:
            return {
                'statusCode': 429,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.',
                    'retry_after': response.headers.get('Retry-After', '10')
                })
            }
        
        # Handle successful response
        if response.status_code in [200, 201]:
            result = response.json()
            return {
                'statusCode': 201,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Candidate created successfully',
                    'candidate_id': result.get('id'),
                    'job_id': candidate['job_id']
                })
            }
        
        # Handle authentication errors
        if response.status_code == 401:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Authentication failed',
                    'message': 'Invalid API token. Please check your Workable API token.'
                })
            }
        
        # Handle forbidden errors (missing scopes)
        if response.status_code == 403:
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Permission denied',
                    'message': 'Your API token is missing required scopes (w_candidates)'
                })
            }
        
        # Handle not found errors
        if response.status_code == 404:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Job not found',
                    'message': f"Job with ID '{candidate['job_id']}' does not exist in Workable"
                })
            }
        
        # Handle other Workable API errors
        error_message = f"Workable API returned status {response.status_code}"
        try:
            error_data = response.json()
            if error_data.get('message'):
                error_message = error_data['message']
            elif error_data.get('error'):
                error_message = error_data['error']
        except:
            pass
        
        return {
            'statusCode': response.status_code,
            'headers': headers,
            'body': json.dumps({
                'error': 'Workable API error',
                'message': error_message,
                'status_code': response.status_code
            })
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'error': 'Invalid JSON',
                'message': 'Request body contains invalid JSON'
            })
        }
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Connection error',
                'message': 'Could not connect to Workable API'
            })
        }
    except requests.exceptions.Timeout as e:
        print(f"Timeout error: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Request timeout',
                'message': 'Workable API request timed out'
            })
        }
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Workable API request failed',
                'message': str(e)
            })
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
    
