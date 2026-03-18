# Workable-ATS-Serverless-API
ATS Integration Microservice built with Python and Serverless Framework. Fetches jobs from Workable, submits candidates, and tracks applications via REST APIs.


## How to create Workable free trial
1. Go to https://www.workable.com/
2. Click "Start free trial"
3. Fill in your details

## How to generate API key/token
1. Login to Workable
2. Settings → Integrations → API
3. Click "Generate new token"
4. Select scopes: r_jobs, w_candidates, r_candidates

## How to run locally
1. Clone repo
2. cd backend
3. Create .env file with:
   WORKABLE_SUBDOMAIN=your-subdomain
   WORKABLE_API_TOKEN=your-token
4. npm install
5. pip install -r requirements.txt
6. serverless offline

## Example curl calls
# GET /jobs
curl http://localhost:3000/dev/jobs

# POST /candidates
curl -X POST http://localhost:3000/dev/candidates \
  -H "Content-Type: application/json" \
  -d '{"name":"John","email":"john@test.com","job_id":"your_jobid_here"}'

# GET /applications
curl http://localhost:3000/dev/applications?job_id=your_jobid_here

