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

Here is an example of the output from testing some real life data: https://gist.github.com/makmanalp/5ebcacdcf6c541bdd549


Usage on HMDC Cluster
=====================

The latest version of reckoner is already installed. All you have to do is to add a shortcut to save you some typing in the future:

- From the HMDC menu on top, go to "RCE Powered Applications" and run "RCE shell".
- Run `echo "alias reckoner='python ~/shared_space/cidgrowlab/reckoner/reckoner.py'" >> ~/.bashrc`.

After you've done that once, you can just do:

- Run `reckoner /path/to/definition_file.yml`!


Tutorial
=======

This will take you through creating a definition file. Let's say that we have an imports / exports dataset with the following files:

```
ecomplexity_aduanas_est_2009.dta
ecomplexity_aduanas_est_2010.dta
ecomplexity_aduanas_est_2011.dta
ecomplexity_aduanas_est_2012.dta
ecomplexity_aduanas_est_2013.dta
ecomplexity_aduanas_mun_2009.dta
ecomplexity_aduanas_mun_2010.dta
ecomplexity_aduanas_mun_2011.dta
ecomplexity_aduanas_mun_2012.dta
ecomplexity_aduanas_mun_2013.dta
```

The dataset spans from 2009 to 2013, and has state-level (est) and municipality-level (mun) aggregations. Here is what a state-level file looks like:

```
   r_est     p           V     O        rca  M   density       eci       pci  \
0      1  8481    35594147  2255   1.755682  1  0.074099  0.741174  1.049106
1      1  7326    19431734  3620   1.611489  1  0.073593  0.741174  2.243703
2      1  6217     1872290   394  13.466545  1  0.087559  0.741174  0.965384
3      1  3922     4565764   609   5.135397  1  0.076310  0.741174  0.736752
4      1  8703  1530602882   236   7.222218  1  0.079454  0.741174 -0.203337

   diversity  ubiquity       coi  cog    av_ubq  tag
0         85        12  0.140593   -0  6.964706    1
1         85         8  0.140593    0  6.964706    0
2         85        12  0.140593   -0  6.964706    0
3         85         5  0.140593   -0  6.964706    0
4         85         6  0.140593   -0  6.964706    0

```

And similarly, here is the first few lines from a municipality level file:

```
   r_mun     p       V   O        rca  M   density       eci       pci  \
0   1001  9604   45532  52  18.727618  1  0.056984  0.788259  0.602146
1   1001  6005   76596   8   1.681844  1  0.057327  0.788259  1.009766
2   1001  9803   37356   7  58.097737  1  0.057033  0.788259  1.359651
3   1001  2206   67990   9   5.490546  1  0.056710  0.788259  0.497866
4   1001  7606  147111  17   1.566195  1  0.056725  0.788259  1.026747

   diversity  ubiquity       coi  cog     av_ubq  tag
0         69        14  1.495513    0  29.376812    1
1         69        30  1.495513    0  29.376812    0
2         69         2  1.495513    0  29.376812    0
3         69        11  1.495513    0  29.376812    0
4         69        31  1.495513    0  29.376812    0
```

R_est and r_mun specify a state or a municipality code, p is a product code, V is the total amount of exports for that product in dollars, and there are a bunch of other variables.

Reckoner requires a definition file for each dataset you want to check. The
format is mostly `attribute_name:value`, with tabs to indicate sub elements and
dashes to indicate list items.

Specifying the dataset
----------------------

Here is the beginning of a real definition file:


```yaml
name: mexico_aduanas_imports
description: Trade data (imports) for Mexico between 1992-1997
source: INEGI
type: ecomplexity
file_pattern: ecomplexity_aduanas_{location}_{year}.dta
```

- **name, description, source**: Just metadata, not used for checking.

- **type**: There are a few preset ones. Ecomplexity is one that matches
the output of our own STATA ecomplexity command. The types of checks that can
be automatically run depend on the file type.

- **pattern**: Defines all the files in your dataset. It's
assumed that all your files have a uniform naming scheme. The parts between
braces like `{location}` are a wildcard match.

In this example, it'll match the filename "ecomplexity_aduanas_est_2012.dta" and determine that for that file,
`location` must be equal to `est` and `year` must be `2012`. Since we didn’t provide a wildcard in the filename for entities (in our case products), it will assume that there is only one level of product aggregation.

Specifying field names
----------------------

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

For each field, the part on the left of the colon
is the field we’re expecting, and the one on the right is what it’s called in
the files.

Don’t forget the indentation! Four spaces.

Wildcards
---------

Field names can contain the wildcards that you specified in the file pattern, like `{location}`. This is useful because sometimes similar fields can be called different things in different files depending on the file type.

As an example, in this case the location is set
to `r_{location}` which renders to `r_mun` in municipality files (e.g.
ecomplexity_aduanas_mun_2009.dta) and `r_est` in state files (e.g.
ecomplexity_aduanas_est_2012.dta)

Generated Fields
----------------

It’s also okay if a field is missing if it will have a single value. We can
automatically fill in the value of that field for each file.

In this case `year` is in `generated_fields`. This gets around the issue that there
isn’t a `year` column in the file, so it just fills it in from the file name
wildcard again.

Classifications
---------------

OK, now what are the locations, entities and years going to be checked against?
You need to specify the classifications:

```yaml
classifications:
    entity:
        hs4_4digit:
            file: /Users/makmana/ciddata/mali_metadata/hs4.tsv
            code_field: Code
            name_field: hs4_name_en
            digits: 4
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
```

As you can see, I’ve specified two different kinds of classifications, for the
location and entity fields. For locations, I made sure the names match the file
wildcards (est and mun), and for entity it doesn’t matter what it’s called
since there is no entity wildcard in the file pattern. HS is only one so that
one will be used.

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

location_entity_value
---------------------
A row from such a dataset would say, for example, "Germany (location) exported 5m dollars (value) worth of bicycles (entity)" or "Bogotá (location) has 50000 (value) workers in the medical industry (entity)".

- Fields that can have different levels of aggregation:
  * location: a location code, at any aggregation level
  * entity: a product, industry, occupation code, or whatever else you might be using.
- Other fields:
  * time: Time period identifier, usually a year like “2009”
  * value: the amount, whether in dollars, or currency, or number of workers, etc.

ecomplexity
-----------
Matches the output of the STATA `ecomplexity` command used at CID (some docs here: https://code.google.com/p/ecomplexity/source/browse/ecomplexity.sthlp)

- Must have all the fields that CPY has, plus: 
  * eci
  * pci
  * rca
  * diversity
  * density
  * ubiquity: Ubiquity of an entity 
  * average_ubiquity: Average ubiquity of the entities of a region 
  * coi: complexity outlook index (i.e. opportunity value)
  * cog: complexity outlook gain (i.e. opportunity gain)
