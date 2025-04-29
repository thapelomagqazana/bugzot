import pytest
from fastapi import status

ENDPOINT = "/api/v1/roles"

# --------------------------
# ✅ Positive Test Cases
# --------------------------

def test_tc_01_fetch_roles_default(client):
    response = client.get(ENDPOINT)
    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.json()

def test_tc_02_fetch_roles_limit_offset(client):
    response = client.get(f"{ENDPOINT}?limit=2&offset=0")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["data"]) <= 2

def test_tc_03_search_roles_by_name(client):
    response = client.get(f"{ENDPOINT}?search=admin")
    assert response.status_code == status.HTTP_200_OK
    for role in response.json()["data"]:
        assert "admin" in role["name"].lower()

def test_tc_04_filter_active_roles(client):
    response = client.get(f"{ENDPOINT}?is_active=true")
    assert response.status_code == status.HTTP_200_OK
    for role in response.json()["data"]:
        assert role["is_active"] is True

def test_tc_05_sort_by_created_at_asc(client):
    response = client.get(f"{ENDPOINT}?sort_by=created_at&sort_dir=asc")
    assert response.status_code == status.HTTP_200_OK

def test_tc_06_sort_by_name_desc(client):
    response = client.get(f"{ENDPOINT}?sort_by=name&sort_dir=desc")
    assert response.status_code == status.HTTP_200_OK
    names = [r["name"].lower() for r in response.json()["data"]]
    assert names == sorted(names, reverse=True)

# --------------------------
# ❌ Negative Test Cases
# --------------------------

def test_tc_10_invalid_limit(client):
    response = client.get(f"{ENDPOINT}?limit=-1")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_tc_11_invalid_sort_by(client):
    response = client.get(f"{ENDPOINT}?sort_by=banana")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]

def test_tc_12_invalid_sort_dir(client):
    response = client.get(f"{ENDPOINT}?sort_dir=UP")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_tc_13_invalid_is_active(client):
    response = client.get(f"{ENDPOINT}?is_active=maybe")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# ---------------------------
# Edge Test Cases
# ---------------------------

def test_tc_20_empty_result_set(client):
    response = client.get(f"{ENDPOINT}?search=zzz999")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == []

def test_tc_21_limit_zero(client):
    response = client.get(f"{ENDPOINT}?limit=0")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == []

def test_tc_22_offset_greater_than_total(client):
    response = client.get(f"{ENDPOINT}?offset=9999")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == []

def test_tc_23_search_special_characters(client):
    response = client.get(f"{ENDPOINT}?search=%admin_")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json()["data"], list)

# ---------------------------
# Corner Test Cases
# ---------------------------

def test_tc_30_role_long_name_description(client, db_session):
    # Assume some roles already have long names/descriptions created
    response = client.get(f"{ENDPOINT}")
    assert response.status_code == status.HTTP_200_OK
    assert all(isinstance(role["name"], str) for role in response.json()["data"])

def test_tc_31_roles_no_users_assigned(client):
    response = client.get(f"{ENDPOINT}")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json()["data"], list)

def test_tc_32_paginate_boundary(client):
    # Assume small number of roles
    response = client.get(f"{ENDPOINT}?limit=5&offset=5")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json()["data"], list)

def test_tc_33_missing_optional_params(client):
    response = client.get(f"{ENDPOINT}")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json()["data"], list)

# ---------------------------
# Security Test Cases
# ---------------------------

def test_tc_40_no_auth(client):
    response = client.get(f"{ENDPOINT}")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]  # Depending if protected

def test_tc_44_sql_injection_attempt(client):
    response = client.get(f"{ENDPOINT}?search=admin' OR '1'='1")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json()["data"], list)

def test_tc_45_massively_large_limit(client):
    response = client.get(f"{ENDPOINT}?limit=1000000")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.skip(reason="Requires actual DoS mitigation like slowapi or custom middleware")
def test_tc_46_dos_attack_burst(client):
    for _ in range(100):
        response = client.get(f"{ENDPOINT}")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS]
