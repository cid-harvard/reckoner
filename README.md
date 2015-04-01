Reckoner
========

Reckoner is a dataset checker. You give it a dataset definition file that helps
it figure out what each column means, and then it:

- Shows you null value counts
- Tells you whether the format matches across files
- Shows you how well identifier columns match an actual classification (e.g.
  valid zip codes, product codes)
- Shows you nonmatching identifiers
- etc.


Installation
============

- In a command line, run `curl https://raw.githubusercontent.com/cid-harvard/reckoner/master/reckoner.py > reckoner.py` to download the script.
- Create a definition file in the same directory as your dataset
- Then run it with `python tester.py path/to/your/definition_file_name.yml`


Example
=======

Reckoner requires a yaml file for each dataset you want to check. The format is
mostly `attribute_name:value`, with tabs to indicate sub elements and dashes to
indicate list items. Here is the beginning of a real definition file:


```yaml
name: mexico_aduanas_imports
description: Trade data (imports) for Mexico between 1992-1997
source: INEGI
type: ecomplexity
file_pattern: ecomplexity_aduanas_{location}_{year}.dta
```

The first three fields are just general descriptions. The fourth field,
however, defines all the files in your dataset. It's assumed that all your
files have a uniform naming scheme. The parts between braces like `{location}`
are a wildcard match. So, for example, it'll match the filename
"ecomplexity_aduanas_est_2012.dta" and determine that for that file, `location`
must be equal to `est` and `year` must be `2012`.

Since we didn’t provide a wildcard in the filename for entities (in our case
products), it will assume that there is only one level of product aggregation.

So now we can start specifying the field names:

```yaml
fields:
    location: "r_{location}"
    entity: p
    value: V
    eci: eci
    pci: pci
    rca: rca
    diversity: diversity
    density: density
    ubiquity: ubiquity
    average_ubiquity: av_ubq
    coi: coi
    cog: cog
generated_fields:
    year: "{year}"
```

Don’t forget the indentation. For each field, the part on the left of the colon
is the field we’re expecting, and the one on the right is what it’s called in
the files.

Fields can be called different things in different files, and this is okay as
long as it matches the file name wildcards - in this case the location is set
to `r_{location}` which renders to `r_mun` in municipality files (e.g.
ecomplexity_aduanas_mun_2009.dta) and `r_est` in state files (e.g.
ecomplexity_aduanas_est_2012.dta)

It’s also okay if a field is missing if it will have a single value: In this
case `year` is in `generated_fields`. This gets around the issue that there
isn’t a `year` column in the file, so it just fills it in from the file name
wildcard again.

You can use this online [tester](http://yaml-online-parser.appspot.com/) to
make sure your definition file is being parsed correctly.

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
