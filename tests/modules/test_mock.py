"""Tests for API mock generation."""

from rigor.modules.mock import generate_mock_server, parse_api_spec


def test_parse_yaml_openapi_spec(tmp_path):
    spec = tmp_path / "openapi.yaml"
    spec.write_text(
        """
openapi: 3.0.0
paths:
  /users/{user_id}:
    get:
      summary: Get user
      responses:
        "200":
          content:
            application/json:
              schema:
                type: object
                properties:
                  email:
                    type: string
                    format: email
""",
        encoding="utf-8",
    )

    endpoints = parse_api_spec(str(spec))

    assert endpoints[0]["path"] == "/users/{user_id}"
    assert endpoints[0]["mock_data"]["email"] == "user@example.com"


def test_generate_flask_mock_converts_path_params(tmp_path):
    spec = tmp_path / "openapi.yaml"
    output_dir = tmp_path / "mock"
    spec.write_text(
        """
openapi: 3.0.0
paths:
  /users/{user_id}:
    get:
      responses:
        "200":
          content:
            application/json:
              schema:
                type: object
""",
        encoding="utf-8",
    )

    output_file = generate_mock_server(str(spec), str(output_dir), "flask")

    content = (output_dir / "mock_server.py").read_text(encoding="utf-8")
    assert output_file.endswith("mock_server.py")
    assert "/users/<user_id>" in content
    assert "def mock_get_users_user_id" in content
