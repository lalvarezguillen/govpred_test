'''
Some unit testing
'''
import os
import datetime
from scrapy.http import Request, TextResponse
from scrapy import FormRequest
from fara_scraper import FARAScraper

def mock_response(url, filename, include_meta=False):
    '''
    @description: produce a fake scrapy response, for the purpose of testing.
    @arg url: {str} the url that prouced the response
    @arg filename: {str} the html file that will act as response body
    @return: {scrapy.TextResponse} fake response for testing.
    '''
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, "r") as html_file:
        file_content = html_file.read()
    request = Request(url=url)
    if include_meta:
        request.meta["principal_data"] = {"some":"data"}
    response = TextResponse(
        url=url,
        request=request,
        body=file_content,
        encoding='utf-8'
    )
    return response
    
    
def mock_row(row_index):
    response = mock_response(
        "https://www.initialrequest.com",
        "Active_Foreign_Principals_mock.html"
    )
    row = response.css("table.apexir_WORKSHEET_DATA tr")[row_index]
    return row
    
    
def test_initial_parse():
    fara_s = FARAScraper()
    initial_response = mock_response(
        "https://www.initialrequest.com",
        "Active_Foreign_Principals_mock.html"
    )
    result = next(fara_s.parse(initial_response))
    assert isinstance(result, FormRequest)
    

class TestGetRequiredFormData():
    fara_s = FARAScraper()
    initial_response = mock_response(
        "https://www.initialrequest.com",
        "Active_Foreign_Principals_mock.html"
    )
    result = fara_s.get_required_form_data(initial_response, 200)
    
    def test_p_widget_num_return(self):
        assert self.result["p_widget_num_return"] == 200
        
    def test_p_instance(self):
        assert self.result["p_instance"] == "7852346389386"
        
    def test_p_flow_id(self):
        assert self.result["p_flow_id"] == "171"
        
    def test_p_flow_step_id(self):
        assert self.result["p_flow_step_id"] == "130"
        
    def test_p_widget_action_mod(self):
        expected = "pgR_min_row=0max_rows=200rows_fetched=0"
        assert self.result["p_widget_action_mod"] == expected
        
    def test_x01(self):
        assert self.result["x01"] == "80340213897823017"
        
    def test_x02(self):
        assert self.result["x02"] == "80341508791823021"
        
        
        
def test_entries_count():
    fara_s = FARAScraper()
    initial_response = mock_response(
        "https://www.initialrequest.com",
        "Active_Foreign_Principals_mock.html"
    )
    result = fara_s.get_entries_count(initial_response)
    assert result == "511"
    

def test_parse_entries():
    fara_s = FARAScraper()
    initial_response = mock_response(
        "https://www.initialrequest.com",
        "Active_Foreign_Principals_mock.html"
    )
    result = fara_s.parse_entries(initial_response)
    entries = list(result)
    assert len(entries) == 15
    

class TestGetPrincipalData():
    row = mock_row(2)
    fara_s = FARAScraper()
    result = fara_s.get_principal_data(row, "Sovereign Martial State")
    row_data = result.meta["principal_data"]
    
    def test_country(self):
        expected_country = "Sovereign Martial State"
        assert self.row_data["country"] == expected_country
    
    def test_foreign_principal(self):
        expected_fp = "Transformation and Continuity, Ajmal Ghani"
        assert self.row_data["foreign_principal"] == expected_fp
        
    def test_date(self):
        expected_date = datetime.datetime(2014, 5, 5).isoformat()
        assert self.row_data["date"] == expected_date
        
    def test_address(self):
        assert "Kabul" in self.row_data["address"]
        
    def test_state(self):
        assert self.row_data["state"] is None
        
    def test_registrant(self):
        assert self.row_data["registrant"] == "Fenton Communications"
        
    def test_reg_num(self):
        assert self.row_data["reg_num"] == "5945"
        



def test_parse_exhibit_data():
    fara_s = FARAScraper()
    initial_response = mock_response(
        "https://www.initialrequest.com",
        "Foreign_Principal_Details_mock.html",
        include_meta=True
    )
    result = fara_s.parse_exhibit_data(initial_response)
    assert "fara.gov" in result["exhibit_url"]
    
    
def test_parse_empty_exhibit_data():
    fara_s = FARAScraper()
    initial_response = mock_response(
        "https://www.initialrequest.com",
        "Foreign_Principal_Empty_mock.html",
        include_meta=True
    )
    result = fara_s.parse_exhibit_data(initial_response)
    assert result["exhibit_url"] is None
    
    
def test_does_contain_data():
    fara_s = FARAScraper()
    row = mock_row(2)
    result = fara_s._contains_data(row)
    assert result is True
    
def test_does_not_contain_data():
    fara_s = FARAScraper()
    row = mock_row(1)
    result = fara_s._contains_data(row)
    assert not result
    
def test_contains_country():
    fara_s = FARAScraper()
    row = mock_row(4)
    result = fara_s.try_to_get_country(row)
    assert result == "ALBANIA"
    
def test_does_not_contain_country():
    fara_s = FARAScraper()
    row = mock_row(5)
    result = fara_s.try_to_get_country(row)
    assert result is False
    