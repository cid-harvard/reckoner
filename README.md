Reckoner
========

![Moneylender and his wife by Matsys](510px-Quentin_Massys_001.jpg)

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

Reckoner requires a definition file for each dataset you want to check. The
format is mostly `attribute_name:value`, with tabs to indicate sub elements and
dashes to indicate list items. Here is the beginning of a real definition file:


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

OK, now what are the locations, entities and years going to be checked against?
You need to specify the classifications:

```yaml
classifications:
    location:
        mun:
            file: NAMES_INEGI_MUNKEY_V2.dta
            code_fields:
                - name: cve_ent
                  digits: 2
                - name: cve_mun
                  digits: 3
            name_field: nom_mun
            digits: 5
        est:
            file: NAMES_INEGI_MUNKEY_V2.dta
            code_field: cve_ent
            name_field: nom_ent
            digits: 2
    entity:
        hs4_4digit:
            file: /Users/makmana/ciddata/mali_metadata/hs4.tsv
            code_field: Code
            name_field: hs4_name_en
            digits: 4
```

As you can see, I’ve specified two different kinds of classifications, for
locations and for entities. For locations, I made sure the names match the file
wildcards (est and mun), and for entity it doesn’t matter what it’s called
since there is only one and that one will be used.

Each classification has a code_field that specifies the code to be matched in
the file, and a name to match against, so it can show you nice results. It also
asks you for a number of digits and normalizes the codes to that. This is to
prevent issues like 0127 not merging with 127, etc. Reckoner will handle
getting rid of duplicate classification entries for you.

Sometimes you’ll have classification codes that are split into two. The “mun”
classification above does that. It specifies code_fields instead of code_field,
and gives two fields in order that should form the final code: First two digits
are state, next three are municipality.

That’s it!

See the complete example [here](https://github.com/cid-harvard/reckoner/blob/master/examples/mexico_aduanas_exports.yml).

You can use this online [tester](http://yaml-online-parser.appspot.com/) to
to see how your definition would be parsed.

File Types
==========

CPY
---
- Fields that can have different levels of aggregation:
  * location: a location code, at any aggregation level
  * entity: a product, industry, occupation code, or whatever else you might be using.
- Other fields:
  * time: Time period identifier, usually a year like “2009”
  * value: the amount, whether in dollars, or currency, or number of workers, etc.

Ecomplexity
-----------
- Must have all the fields that CPY has, plus: 

Reference
=========

type
---
