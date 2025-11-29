# The North Jersey Project - Tony Soprano Chatbot Frontend


## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure API Endpoint

Create a `.env` file in the root directory:

```bash
cp .env
```

Then edit `.env` and add your GKE API endpoint:

```
NEXT_PUBLIC_API_ENDPOINT=http://your-gke-service-url/generate
```

### 3. Run Locally

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.