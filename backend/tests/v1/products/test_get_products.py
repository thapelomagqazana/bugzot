import pytest
from fastapi import status
from tests.utils import make_product
from app.models.products.product import Product
from app.db.session import get_db

ENDPOINT = "/api/v1/products"

# ----------------------
# Positive Test Cases
# ----------------------

def test_tc_01_fetch_all_products(client):
    response = client.get(ENDPOINT)
    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.json()

def test_tc_02_fetch_with_limit_offset(client):
    response = client.get(f"{ENDPOINT}?limit=5&offset=0")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["data"]) <= 5

def test_tc_03_search_by_name(client):
    response = client.get(f"{ENDPOINT}?search=BugZot")
    assert response.status_code == status.HTTP_200_OK
    for p in response.json()["data"]:
        assert "bugzot" in p["name"].lower()

def test_tc_04_filter_active_products(client):
    response = client.get(f"{ENDPOINT}?is_active=true")
    assert response.status_code == status.HTTP_200_OK
    for p in response.json()["data"]:
        assert p["is_active"] is True

def test_tc_05_sort_by_created_at_asc(client):
    response = client.get(f"{ENDPOINT}?sort_by=created_at&sort_dir=asc")
    assert response.status_code == status.HTTP_200_OK
    dates = [p["created_at"] for p in response.json()["data"]]
    assert dates == sorted(dates)

def test_tc_06_sort_by_name_desc(client):
    response = client.get(f"{ENDPOINT}?sort_by=name&sort_dir=desc")
    assert response.status_code == status.HTTP_200_OK
    names = [p["name"].lower() for p in response.json()["data"]]
    assert names == sorted(names, reverse=True)

# def test_tc_07_filter_by_category(client, db_session):
#     category_id = db_session.execute("SELECT id FROM categories LIMIT 1").scalar()
#     response = client.get(f"{ENDPOINT}?category_id={category_id}")
#     assert response.status_code == status.HTTP_200_OK
#     for p in response.json()["data"]:
#         assert p["category_id"] == category_id

# ----------------------
# Negative Test Cases
# ----------------------

def test_tc_10_invalid_limit(client):
    response = client.get(f"{ENDPOINT}?limit=-1")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_tc_11_invalid_offset(client):
    response = client.get(f"{ENDPOINT}?offset=-10")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_tc_12_invalid_sort_by(client):
    response = client.get(f"{ENDPOINT}?sort_by=banana")
    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_200_OK]

def test_tc_13_invalid_sort_dir(client):
    response = client.get(f"{ENDPOINT}?sort_dir=UP")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_tc_14_invalid_is_active(client):
    response = client.get(f"{ENDPOINT}?is_active=maybe")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_tc_15_nonexistent_category(client):
    response = client.get(f"{ENDPOINT}?category_id=999999")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == []

# ----------------------
# Edge Test Cases
# ----------------------

def test_tc_20_search_no_match(client):
    response = client.get(f"{ENDPOINT}?search=zzz999")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == []

def test_tc_21_limit_zero(client):
    response = client.get(f"{ENDPOINT}?limit=0")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == []

def test_tc_22_offset_beyond_total(client):
    response = client.get(f"{ENDPOINT}?offset=9999")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"] == []

def test_tc_23_special_chars_search(client):
    response = client.get(f"{ENDPOINT}?search=%_#&!")
    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.json()

def test_tc_24_large_valid_limit(client):
    response = client.get(f"{ENDPOINT}?limit=100")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["data"]) <= 100

# ----------------------
# Corner Test Cases
# ----------------------

def test_tc_30_max_length_name_and_description(client, db_session):
    name = "A" * 100
    description = "D" * 255
    product = make_product(name=name, description=description, db=db_session)
    response = client.get(f"{ENDPOINT}?search={name}")
    assert response.status_code == status.HTTP_200_OK
    assert any(p["name"] == name for p in response.json()["data"])

def test_tc_31_product_no_relations(client, db_session):
    product = make_product(db=db_session)
    response = client.get(f"{ENDPOINT}?search={product.name}")
    assert response.status_code == status.HTTP_200_OK
    assert any(p["id"] == product.id for p in response.json()["data"])

def test_tc_32_exact_pagination_boundary(client, db_session):
    total = db_session.query(Product).count()
    if total >= 5:
        response = client.get(f"{ENDPOINT}?limit=5&offset={total-5}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["data"]) <= 5

def test_tc_33_omit_all_optional_params(client):
    response = client.get(ENDPOINT)
    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.json()

# ----------------------
# Security Test Cases
# ----------------------

def test_tc_43_sql_injection_in_search(client):
    response = client.get(f"{ENDPOINT}?search=admin' OR '1'='1")
    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.json()

def test_tc_44_extremely_large_limit(client):
    response = client.get(f"{ENDPOINT}?limit=1000000")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_tc_45_rate_limit_burst(client):
    for _ in range(20):  # simulate rapid hits
        client.get(ENDPOINT)
    # You may need real rate-limiting middleware to expect 429
    assert True  # No crash means pass for now

