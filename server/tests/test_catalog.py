"""Product browsing/search (A04 injection) and reviews (A05 abuse of reviews)."""
from conftest import place_order
from extensions import db
from models import Product, Review


def test_lists_active_products_with_pagination(client):
    data = client.get("/products?per_page=5&page=2").get_json()
    assert data["total"] == 22 and data["page"] == 2 and len(data["items"]) == 5


def test_search_and_filters(client):
    data = client.get("/products?q=boot").get_json()
    assert [p["slug"] for p in data["items"]] == ["fern-trail-boot"]
    data = client.get("/products?category=Ceramics&max_price=50").get_json()
    assert {p["slug"] for p in data["items"]} == {"chalk-stoneware-mug", "porcelain-cup-pair"}
    prices = [p["price"] for p in client.get("/products?sort=price_desc").get_json()["items"]]
    assert prices == sorted(prices, reverse=True)


def test_sql_injection_attempts_are_treated_as_text(client):
    for payload in ["' OR 1=1 --", "\" OR \"\"=\"", "x'; DROP TABLE products; --", "%", "_"]:
        resp = client.get("/products", query_string={"q": payload})
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 0, payload
    assert Product.query.count() == 22


def test_invalid_query_parameters_are_rejected(client):
    assert client.get("/products?category=Weapons").status_code == 400
    assert client.get("/products?per_page=1000").status_code == 400
    assert client.get("/products?sort=name;drop").status_code == 400
    assert client.get("/products?unexpected=1").status_code == 400


def test_archived_product_is_hidden(client):
    Product.query.filter_by(slug="moss-lamp").update({"is_active": False})
    db.session.commit()
    assert client.get("/products/moss-lamp").status_code == 404
    assert all(p["slug"] != "moss-lamp" for p in client.get("/products").get_json()["items"])


def _buy(c, slug="chalk-stoneware-mug"):
    ref = place_order(c, [{"slug": slug, "quantity": 1}]).get_json()["order"]["reference"]
    c.post(f"/payments/simulated/{ref}", {"outcome": "success"})


def test_review_requires_purchase(customer_client):
    resp = customer_client.post("/products/chalk-stoneware-mug/reviews", {"rating": 5})
    assert resp.status_code == 403 and resp.get_json()["code"] == "not_purchased"


def test_review_lifecycle(customer_client, admin_client, client):
    _buy(customer_client)
    resp = customer_client.post("/products/chalk-stoneware-mug/reviews", {"rating": 4, "review_text": "Nice"})
    assert resp.status_code == 201 and resp.get_json()["review"]["status"] == "pending"
    review_id = resp.get_json()["review"]["review_id"]

    # Pending reviews aren't public
    assert client.get("/products/chalk-stoneware-mug/reviews").get_json()["items"] == []
    # Only one review per product
    assert customer_client.post("/products/chalk-stoneware-mug/reviews", {"rating": 5}).status_code == 409

    admin_client.patch(f"/admin/reviews/{review_id}", {"status": "approved"})
    public = client.get("/products/chalk-stoneware-mug/reviews").get_json()
    assert public["items"][0]["review_text"] == "Nice" and public["review_count"] == 1 and public["rating"] == 4.0
    assert "user_id" not in public["items"][0] and "email" not in str(public)

    # Editing sends it back for moderation
    edited = customer_client.patch(f"/reviews/{review_id}", {"rating": 2}).get_json()["review"]
    assert edited["status"] == "pending" and edited["rating"] == 2
    assert client.get("/products/chalk-stoneware-mug/reviews").get_json()["review_count"] == 0

    assert customer_client.delete(f"/reviews/{review_id}").status_code == 200
    assert db.session.get(Review, review_id) is None


def test_review_input_is_validated(customer_client):
    _buy(customer_client)
    for bad in [{"rating": 0}, {"rating": 6}, {"rating": "5"}, {"rating": 5, "review_text": "x" * 2001},
                {"rating": 5, "status": "approved"}]:
        assert customer_client.post("/products/chalk-stoneware-mug/reviews", bad).status_code == 400, bad


def test_review_text_is_stored_verbatim_not_executed(customer_client, admin_client, client):
    """Output encoding happens in the frontend (React escapes text); the API stores text as data."""
    _buy(customer_client)
    script = "<script>alert('x')</script>"
    rid = customer_client.post("/products/chalk-stoneware-mug/reviews",
                               {"rating": 5, "review_text": script}).get_json()["review"]["review_id"]
    admin_client.patch(f"/admin/reviews/{rid}", {"status": "approved"})
    resp = client.get("/products/chalk-stoneware-mug/reviews")
    assert resp.content_type == "application/json"
    assert resp.get_json()["items"][0]["review_text"] == script


def test_cannot_edit_someone_elses_review(customer_client, new_client, make_user):
    _buy(customer_client)
    rid = customer_client.post("/products/chalk-stoneware-mug/reviews", {"rating": 5}).get_json()["review"]["review_id"]
    other = make_user(email="other@example.com")
    c = new_client()
    c.login(other.email)
    assert c.patch(f"/reviews/{rid}", {"rating": 1}).status_code == 404
    assert c.delete(f"/reviews/{rid}").status_code == 404
