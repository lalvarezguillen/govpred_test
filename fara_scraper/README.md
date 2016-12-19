This is Luis' solution to the FARAS scraper challenge.

The only setup required is installing requirements.

```
sudo pip install -r requirements.txt
```

To make sure everything is working fine, you can run the tests included. Calling
pytest from within the project's directory
```
cd govpredict_test
pytest
```

To actually run the scraper, use the scrapy runspider command. Optionally passing
an output argument

```
scrapy runspider fara_scraper.py -o my_output_file.json
```