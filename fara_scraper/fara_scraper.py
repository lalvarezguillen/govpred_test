'''
Luis' solution to the GovPredict's Interview Test. 
'''
import datetime
import scrapy

class FARAScraper(scrapy.Spider):
    '''
    Spider to pull info about active Foreign Principals from fara.gov.
    
    First, it hits self.start_url to obtain a bunch of parameters, that will be
    required by the rest of the requests. This initial request also obtains the
    total number of active Foreign Principals.
    
    Then, it requests all the active Foreign Principals, in a single page.
    
    Finally, the page of each Foreign Principal is visited, to obtain its
    exhibit url. And the info is returned.
    '''
    name = "FARA Scraper"
    start_urls = [
        "https://efile.fara.gov/pls/apex/f?p=171:130:0::NO:RP,130:P130_DATERANGE:N"
        ]
    base_url = "https://efile.fara.gov/pls/apex/"
    
    def parse(self, response):
        '''
        @description: handles the response of the initial request, to obtain the
        total number of Foreign Principals, and the data that will be required
        for successive requests.
        @arg response: {scrapy.Response} The response produced by the initial
        request.
        @return: queues a request to obtain a page containing all the Foreign
        Principals' info.
        '''
        entries_count = self.get_entries_count(response)
        required_form_data = self.get_required_form_data(response, entries_count)
        entries = self.get_entries_data(required_form_data)
        yield entries
        
        
        
    def get_required_form_data(self, response, entries_count):
        '''
        @description: parses the content of the initial request, to obtain a bunch
        of data that will be required for successive requests.
        @arg response: {scrapy.Response}The response returned by the initial
        request.
        @arg entries_count: {str} the number of Foreign Principals, according to
        the content of the initial request.
        @return: {dict} data to be used as body of the request that will pull
        the info of all Foreign Principals. It asks for a single page result.
        Also contains some sort of session information, required by the site.
        '''
        pflowid = response.css("#pFlowId")[0].root
        pflowstepid = response.css("#pFlowStepId")[0].root
        pinstance = response.css("#pInstance")[0].root
        x01 = response.css("#apexir_WORKSHEET_ID")[0].root
        x02 = response.css("#apexir_REPORT_ID")[0].root
        range_string="pgR_min_row=0max_rows={max_rows}rows_fetched=0".format(
            max_rows=entries_count)
        
        form_data = {
            "p_request":"APXWGT",
            "p_instance": pinstance.value,
            "p_flow_id": pflowid.value,
            "p_flow_step_id": pflowstepid.value,
            "p_widget_num_return": entries_count,
            "p_widget_name":"worksheet",
            "p_widget_mod": "ACTION",
            "p_widget_action": "PAGE",
            "p_widget_action_mod": range_string,
            "x01": x01.value,
            "x02": x02.value
        }
        return form_data
    
    def get_entries_count(self, response):
        '''
        @description: parses the count of Foreign Principals, from the content
        of the response of the initial request.
        @arg response: {scrapy.Response} The response of the initial request.
        @return: {str} The count of Foreign Principals.
        '''
        pagination_data = response.css("span.fielddata")[0].root.text
        return pagination_data.split("of")[1].strip()
    
    def get_entries_data(self, form_data):
        '''
        @description: Obtains a single page containing the information of all
        the Foreign Principals.
        @arg form_data: {dict} data to be used as body of the request.
        @return: {scrapy.FormRequest} queues up the request.
        '''
        r = scrapy.FormRequest(
            self.base_url + "wwv_flow.show",
            headers={"Referer":self.start_urls[0]},
            formdata=form_data,
            callback=self.parse_entries
        )
        return r
        
    def parse_entries(self, response):
        '''
        @description: parses the content of the response of requesting the info
        of all the Foreign Principals. Loops through the rows of the result, 
        extracts country information, and queues up the extraction of Foreign
        Principal information from the rows that contain such info.
        @arg response: {scrapy.Response} result of requesting the info of all
        the Foreign Principals.
        @return: after asigning each Foreing Principal row its country, queues
        up the parsing of the rest of Foreign Principal info.
        '''
        rows = response.css("table.apexir_WORKSHEET_DATA tr")
        for row in rows:
            is_country = self.try_to_get_country(row)
            # I encountered 3 types of rows: rows containing country info, rows
            # containing Foreign Principal info, and useless rows.
            if is_country: # handle country rows
                country = is_country
            elif self._contains_data(row): # handle Foreign Principal row
                yield self.get_principal_data(row, country)

            
    def get_principal_data(self, row, country):
        '''
        @description: parses the info or a Foreign Principal, in a given row.
        Creates an initial version of the dictionary containing most of the Foreign
        Principal info, and queues up a request to obtain the missing part (the 
        url of the exhibit document)
        @arg row: The row containg a particular Foreign Principal's info.
        @arg country: {str} The country of this particular Foreign Principal.
        @return: {scrapy.Request} queues up a request to obtain the Foreign
        Principal's exhibit doc's url.
        '''
        principal_data = {}
        
        url = row.css("a")[0].root.attrib["href"]
        principal_data["url"] = (self.base_url + url) or None 
        
        # using 'or empty string' so it can be str.striped safely
        foreign_principal = row.css("td")[1].root.text_content() or ""
        principal_data["foreign_principal"] = foreign_principal.strip() or None
        
        reg_date = row.css("td")[2].root.text_content() or ""
        reg_date = reg_date.strip() or None
        # Turn the date into an ISO string, if any
        if reg_date:
            month, day, year = reg_date.split("/")
            reg_date = datetime.datetime(
                int(year), int(month.lstrip("0")), int(day.lstrip("0"))    
            )
            reg_date = reg_date.isoformat()
        principal_data["date"] = reg_date or None
        
        address = row.css("td")[3].root.text_content() or ""
        principal_data["address"] = address.strip() or None
        
        state = row.css("td")[4].root.text_content() or ""
        principal_data["state"] = state.strip() or None
        
        registrant = row.css("td")[5].root.text_content() or ""
        principal_data["registrant"] = registrant.strip() or None
        
        reg_num = row.css("td")[6].root.text_content() or ""
        principal_data["reg_num"] = reg_num.strip() or None
        
        country = country or ""
        principal_data["country"] = country.strip() or None
        
        if not url:
            return principal_data
            
        return scrapy.Request(
            principal_data["url"],
            headers={"Referer":self.start_urls[0]},
            meta={"principal_data":principal_data},
            callback=self.parse_exhibit_data
        )
        
        
    def parse_exhibit_data(self, response):
        '''
        @description: parses the data obtained from requesting the exhibit 
        document's url.
        @arg response: {scrapy.Response} the result of requesting the exhibit
        doc's url.
        @return {dict} contains all the info of a particular Foreign Principal.
        '''
        principal_data = response.meta["principal_data"]
        
        doc_url_container = response.css("tr.even")
        if len(doc_url_container)>0:
            doc_url = doc_url_container[0].css("a")[0].root.attrib["href"] or None
        else:
            doc_url = None
            
        principal_data["exhibit_url"] = doc_url
        return principal_data
        
    
    def _contains_data(self, row):
        '''
        @description: checks if a row contains Foreign Principal info, by checking
        if its class is either odd or even.
        @arg row: the class to verify.
        @return: {bool} Whether the row contains Foreign Principal info.
        '''
        if "class" in row.root.attrib:
            class_name = row.root.attrib["class"]
            return class_name == "odd" or class_name == "even"
            
            
    def try_to_get_country(self, row):
        '''
        @description: checks if a given row contains country info. If it does,
        it returns the actual country info, otherwise it returns False.
        @arg row: the column to verify.
        @return: {str of False} the country info if any, else False.
        '''
        country_span = row.root.cssselect("span.apex_break_headers")
        if not country_span:
            return False
        else:
            country = country_span[0].text_content()
            return country
        
