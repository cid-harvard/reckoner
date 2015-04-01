Reckoner
========

Reckoner is a dataset checker. You give it a dataset definition file that helps it figure out what each column means, and then it:

- Shows you null value counts
- Tells you whether the format matches across files
- Shows you how well identifier columns match an actual classification (e.g. valid zip codes, product codes)
- Shows you nonmatching identifiers
- etc.


Installation
============

- Run `curl https://raw.githubusercontent.com/cid-harvard/dataset-compliance/master/tester.py > tester.py` to download the script.
- Then run it with `python tester.py definition_file_name.yml`


Example
=======

Reckoner requires a yaml file for each dataset you want to check. The format is mostly `attribute_name:value`, with tabs to indicate sub elements and dashes to indicate list items. Here is the beginning of a real definition file:

```yaml
name: mexico_aduanas_imports
description: Trade data (imports) for Mexico between 1992-1997
source: INEGI
type: ecomplexity
file_pattern: ecomplexity_aduanas_{location}_{year}.dta
```

The first three fields are just general descriptions. The fourth field, however, defines all the files in your dataset. It's assumed that all your files have a uniform naming scheme. The parts between braces like `{location}` are a wildcard match. So, for example, it'll match the filename "ecomplexity_aduanas_est_2012.dta" and determine that for that file, `location` must be equal to `est` and `year` must be `2012`.


You can use this online [tester](http://yaml-online-parser.appspot.com/) to make sure your definition file is being parsed correctly. 

File Types
==========

CPY
---
- Must have fields: Location, Entity, Value, Year
  * location: a location code, at any aggregation level
  * entity: a product, industry, occupation code, or whatever else you might be using.
  * value: the amount, whether in dollars, or currency, or number of workers, etc.
  * year: four digit year.

Ecomplexity
-----------
- Must have all the fields that CPY has, plus: 

Reference
=========

type
---
