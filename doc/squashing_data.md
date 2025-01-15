# Squashing data

There is a lot of overlap between the TechInfoDepot and WikiDevi data, that
somehow needs to be reconcile. This is not as easy as it seems.

There are a few situations for the TechInfoDepot data (and similarly for
WikiDevi data). For each device the following will be true:

1. there is no recorded link to WikiDevi and no recorded link from WikiDevi
   back to TechInfoDepot
2. there is a recorded link to WikiDevi and no recorded link from WikiDevi
   back to TechInfoDepot
3. there is a recorded link to WikiDevi and a matching recorded link from
   WikiDevi back to TechInfoDepot
4. there is a recorded link to WikiDevi and a non-matching recorded link from
   WikiDevi back to TechInfoDepot
5. there is no recorded link to WikiDevi and a recorded link from WikiDevi back
   to TechInfoDepot

or, when visualising as a graph:

1. A    B
2. A --> B
3. A <--> B
4. A --> B --> C
5. A <-- B

No matter how links were recorded, these should only be treated as (strong)
hints, as the data should be leading.

There is also data from OpenWrt, which seems to be of higher quality, but
because the data available from the OpenWrt CSV dump is less complete than
the TechInfoDepot or WikiDevi data it is merely used to refine the other
data.

## Scenario 1: no link recorded

In this scenario no link between the wikis has been explicitly recorded for a
device, but the devices could still be the same, based on name, type, and so
on.

## Scenario 2: one way recorded link

In this scenario there is only a link from one wiki to the other, but not the
other way around.

This is the inverse of scenario 5 which should be treated similarly.

## Scenario 3: two way recorded link

This should be the strongest case as both wikis have a link to each other.

## Scenario 4: non-matching recorded links

There could be different links recorded. One example of a situation when this
could happen is that a device was renamed on one wiki and the name was not
updated in the other wiki.

## Scenario 5: only a backlink recorded

This is the inverse of scenario 2 and should be treated similarly.
