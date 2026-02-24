import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_static_portal(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert "Experimentation Framework" in response.text

@pytest.mark.asyncio
async def test_static_dashboard(client: AsyncClient):
    response = await client.get("/app")
    assert response.status_code == 200
    assert "AI Framework | Dashboard" in response.text

@pytest.mark.asyncio
async def test_prompt_lifecycle(client: AsyncClient):
    # 1. Create prompt
    payload = {
        "name": "api_test_prompt",
        "content": "You are a test assistant.",
        "author": "tester",
        "tags": {"env": "test"}
    }
    response = await client.post("/api/prompts", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "api_test_prompt"
    assert data["version"] == 1
    
    # 2. List prompts
    response = await client.get("/api/prompts")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    
    # 3. Create second version
    payload["content"] = "You are an updated test assistant."
    response = await client.post("/api/prompts", json=payload)
    assert response.json()["version"] == 2
    
    # 4. Compare versions
    response = await client.get("/api/prompts/api_test_prompt/compare?version_a=1&version_b=2")
    assert response.status_code == 200
    compare_data = response.json()
    assert compare_data["similarity_ratio"] > 0
    assert "unified_diff" in compare_data

@pytest.mark.asyncio
async def test_run_experiment_api(client: AsyncClient):
    # Register a prompt first
    await client.post("/api/prompts", json={
        "name": "exp_prompt",
        "content": "Test prompt",
        "author": "tester"
    })
    
    payload = {
        "name": "API Experiment",
        "prompt_name": "exp_prompt",
        "model_name": "mock-model",
        "temperature": 0.5,
        "test_cases": [
            {"input": "Hello", "expected": "Mock logic based on mock-model processing: 'Hello'"}
        ]
    }
    response = await client.post("/api/experiments", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["accuracy"] == 1.0
    
    # Get by ID
    exp_id = data["id"]
    response = await client.get(f"/api/experiments/{exp_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "API Experiment"

@pytest.mark.asyncio
async def test_ab_test_api(client: AsyncClient):
    # Run two experiments
    async def run_exp(name):
        res = await client.post("/api/experiments", json={
            "name": name,
            "prompt_content": "Static prompt",
            "model_name": "mock-model",
            "test_cases": [{"input": "hi", "expected": "Mock logic based on mock-model processing: 'hi'"}]
        })
        return res.json()["id"]

    id_a = await run_exp("Exp A")
    id_b = await run_exp("Exp B")

    payload = {
        "name": "AB API Test",
        "experiment_a_id": id_a,
        "experiment_b_id": id_b,
        "traffic_split": 0.5,
        "metric_name": "accuracy"
    }
    response = await client.post("/api/ab-tests", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AB API Test"
    assert "p_value" in data

@pytest.mark.asyncio
async def test_report_generation_api(client: AsyncClient):
    # Run experiment
    res = await client.post("/api/experiments", json={
        "name": "Report Exp",
        "prompt_content": "Static",
        "model_name": "mock-model",
        "test_cases": [{"input": "hi", "expected": "bi"}]
    })
    exp_id = res.json()["id"]
    
    # Get report
    response = await client.get(f"/api/reports/{exp_id}")
    assert response.status_code == 200
    assert "report" in response.json()
    
    # Automate report
    response = await client.post(f"/api/reports/experiments/{exp_id}/automate")
    assert response.status_code == 200
    assert "started" in response.json()["message"]
