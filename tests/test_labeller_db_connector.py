import pytest
import urllib.parse
import base64
from sqlalchemy import text

# Import the connector classes using absolute imports.
from services.LabellerDatabaseConnector import (
    LabellerDatabaseConnector,
    NoneDB,
    MYSQLLabellerDatabaseConnector,
)
from services.DataTypes import Labeller

# ================================
# Dummy Engine, Connection, and Result Classes
# ================================

class DummyResultLabellers:
    """
    Dummy result for get_labellers and get_labellers_with_data.
    Expected row layout: (LabellerID, skill, alpha, beta)
    """
    def __init__(self):
        self.rowcount = 1
        self.rows = [("1", "plane", 1.1, 1.0)]
    def __iter__(self):
        return iter(self.rows)

class DummyResultLabellerInfo:
    """
    Dummy result for get_labeller_info_with_data.
    Expected row layout: (LabellerID, <unused>, profile_picture (bytes), first_name, col4, col5, col6, creation_date)
    """
    def __init__(self):
        self.rowcount = 1
        self.rows = [("1", "unused", b"fakeimage", "John", "col4", "col5", "col6", "2023-01-01")]
    def __iter__(self):
        return iter(self.rows)

class DummyConnection:
    def __init__(self):
        self.last_executed = []  # To store executed queries and their parameters.
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute(self, query, params=None):
        self.last_executed.append((str(query), params))
        query_str = str(query)
        if "FROM Labeller_info" in query_str:
            return DummyResultLabellerInfo()
        if "SELECT" in query_str:
            return DummyResultLabellers()
        return None

    def commit(self):
        self.committed = True

class DummyEngine:
    def __init__(self):
        self.last_connection = None

    def connect(self):
        conn = DummyConnection()
        self.last_connection = conn
        return conn

# ================================
# Fixtures for Monkeypatching
# ================================

@pytest.fixture
def dummy_engine():
    return DummyEngine()

@pytest.fixture
def patch_create_engine(monkeypatch, dummy_engine):
    """
    Patch the create_engine call in the LabellerDatabaseConnector module to return our dummy engine.
    """
    import services.LabellerDatabaseConnector as ldc
    monkeypatch.setattr(ldc, "create_engine", lambda url: dummy_engine)

@pytest.fixture(autouse=True)
def patch_env_vars(monkeypatch):
    # Set dummy environment variables needed for the connection.
    monkeypatch.setenv("_LABELDATABASE_MYSQLUSER", "dummy_user")
    monkeypatch.setenv("_LABELDATABASE_MYSQLPASSWORD", "dummy_pass")
    monkeypatch.setenv("_LABELDATABASE_MYSQLHOST", "dummy_host")
    monkeypatch.setenv("_LABELDATABASE_MYSQLDATABASE", "dummy_db")

# ================================
# Tests for the Abstract Base Class and NoneDB
# ================================

def test_abstract_base_instantiation():
    # Instantiating an abstract base class should raise a TypeError.
    with pytest.raises(TypeError):
        LabellerDatabaseConnector()

def test_nonedb_methods():
    none_db = NoneDB()
    # Methods implemented as pass should return None.
    assert none_db.make_db_connection() is None
    assert none_db.push_labeller(None) is None
    assert none_db.get_labellers("SELECT 1") is None
    assert none_db.get_labellers_with_data("SELECT 1", {}) is None

# ================================
# Tests for MYSQLLabellerDatabaseConnector
# ================================

def test_push_labeller(monkeypatch, patch_create_engine, dummy_engine):
    connector = MYSQLLabellerDatabaseConnector()
    test_labeller = Labeller(LabellerID="1", skill="plane", alpha=1.1, beta=1.0)
    connector.push_labeller(test_labeller)
    conn = dummy_engine.last_connection
    # Ensure commit was called.
    assert conn.committed is True
    # Check that an INSERT query was executed.
    insert_queries = [q for q, params in conn.last_executed if "INSERT INTO Labeller_skills" in q]
    assert len(insert_queries) > 0
    # Optionally, verify that the parameters contain the expected labeller values.
    for query, params in conn.last_executed:
        if "INSERT INTO Labeller_skills" in query:
            expected_data = {
                "labeller_id": test_labeller.LabellerID,
                "skill": test_labeller.skill,
                "alpha": test_labeller.alpha,
                "beta": test_labeller.beta,
            }
            assert params == expected_data
            break

def test_get_labellers(monkeypatch, patch_create_engine, dummy_engine):
    connector = MYSQLLabellerDatabaseConnector()
    query = "SELECT * FROM Labeller_skills WHERE Labeller_id = '1';"
    labellers = connector.get_labellers(query)
    # Verify that one Labeller is returned with the expected dummy data.
    assert isinstance(labellers, list)
    assert len(labellers) == 1
    labeller_obj = labellers[0]
    assert labeller_obj.LabellerID == "1"
    assert labeller_obj.skill == "plane"
    assert labeller_obj.alpha == 1.1
    assert labeller_obj.beta == 1.0

def test_get_labellers_with_data(monkeypatch, patch_create_engine, dummy_engine):
    connector = MYSQLLabellerDatabaseConnector()
    query = "SELECT * FROM Labeller_skills WHERE Labeller_id = :labeller_id;"
    data = {"labeller_id": "1"}
    labellers = connector.get_labellers_with_data(query, data)
    # Verify that one Labeller is returned with the expected dummy data.
    assert isinstance(labellers, list)
    assert len(labellers) == 1
    labeller_obj = labellers[0]
    assert labeller_obj.LabellerID == "1"
    assert labeller_obj.skill == "plane"
    assert labeller_obj.alpha == 1.1
    assert labeller_obj.beta == 1.0

def test_get_labeller_info_with_data(monkeypatch, patch_create_engine, dummy_engine):
    connector = MYSQLLabellerDatabaseConnector()
    # Use a dummy query that our DummyConnection recognizes.
    query = "SELECT * FROM Labeller_info WHERE Labeller_id = :labeller_id;"
    data = {"labeller_id": "1"}
    info = connector.get_labeller_info_with_data(query, data)
    # Verify that info is a list with one dictionary containing the expected keys.
    assert isinstance(info, list)
    assert len(info) == 1
    info_dict = info[0]
    # The profile picture should be base64 encoded.
    expected_encoded = base64.b64encode(b"fakeimage").decode("utf-8")
    assert info_dict["profile_picture"] == expected_encoded
    assert info_dict["first_name"] == "John"
    assert info_dict["creation_date"] == "2023-01-01"
