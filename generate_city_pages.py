#!/usr/bin/env python3
"""Oregon Information - site generator.

Builds every city page, every county page, the cities A-Z directory, the About /
Contact / Privacy pages, sitemap.xml and robots.txt from:
  data/cities.json    (241 incorporated cities: 2020/2010 Census, area, incorporation,
                       coordinates, official website, Wikipedia summary + photo)
  data/counties.json  (36 counties)
  custom_city_content.json (optional hand-written extras, keyed like "portland")
Data refresh: python3 data/gather.py   |   Build: python3 generate_city_pages.py
"""

import html, json, math, os, re, shutil
from datetime import date

BASE_URL     = 'https://oregoninformation.com'
SITE_NAME    = 'Oregon Information'
CONTACT_EMAIL = 'contact@oregoninformation.com'
ANALYTICS_ID = ''
OUT          = '.'
TODAY        = date.today().isoformat()
DEFAULT_IMG  = f'{BASE_URL}/assets/og-image.png'
SLUG_OVERRIDES = {'Mt. Angel': 'mount-angel'}   # keep existing URL

COUNTY_INFO = {
 'Multnomah':('Portland Metro','Portland General Electric'),'Washington':('Portland Metro','Portland General Electric'),
 'Clackamas':('Portland Metro','Portland General Electric'),'Columbia':('Northwest Oregon','Portland General Electric'),
 'Clatsop':('North Coast','Pacific Power'),'Tillamook':('North Coast','Tillamook PUD'),
 'Yamhill':('Willamette Valley','Portland General Electric'),'Marion':('Willamette Valley','Portland General Electric'),
 'Polk':('Willamette Valley','Portland General Electric / Pacific Power'),'Linn':('Willamette Valley','Pacific Power'),
 'Benton':('Willamette Valley','Pacific Power'),'Lane':('Willamette Valley','EWEB / Pacific Power'),
 'Lincoln':('Central Coast','Central Lincoln PUD'),'Douglas':('Southwest Oregon','Pacific Power / Douglas Electric Cooperative'),
 'Coos':('South Coast','Pacific Power / Coos-Curry Electric Cooperative'),'Curry':('South Coast','Coos-Curry Electric Cooperative'),
 'Josephine':('Rogue Valley','Pacific Power'),'Jackson':('Rogue Valley','Pacific Power'),
 'Klamath':('South Central Oregon','Pacific Power'),'Lake':('South Central Oregon','Pacific Power / Surprise Valley Electric'),
 'Deschutes':('Central Oregon','Pacific Power / Central Electric Cooperative'),'Jefferson':('Central Oregon','Pacific Power'),
 'Crook':('Central Oregon','Pacific Power'),'Hood River':('Columbia River Gorge','Pacific Power'),
 'Wasco':('Columbia River Gorge','Northern Wasco County PUD'),'Sherman':('North Central Oregon','Wasco Electric Cooperative'),
 'Gilliam':('North Central Oregon','Columbia Basin Electric Cooperative'),'Morrow':('North Central Oregon','Umatilla Electric Cooperative'),
 'Umatilla':('Eastern Oregon','Pacific Power / Umatilla Electric Cooperative'),'Union':('Northeast Oregon','Oregon Trail Electric Cooperative'),
 'Wallowa':('Northeast Oregon','Pacific Power'),'Baker':('Northeast Oregon','Oregon Trail Electric Cooperative'),
 'Grant':('Eastern Oregon','Oregon Trail Electric Cooperative'),'Harney':('Southeast Oregon','Harney Electric Cooperative'),
 'Malheur':('Southeast Oregon','Idaho Power'),'Wheeler':('North Central Oregon','Columbia Power Cooperative'),
}

COUNTY_ELECTIONS = {
 'Baker':     'https://bakercounty.org/departments/elections',
 'Benton':    'https://www.bentoncountyor.gov/elections/',
 'Clackamas': 'https://www.clackamas.us/elections',
 'Clatsop':   'https://www.clatsopcounty.gov/237/Elections-Filing',
 'Columbia':  'https://www.columbiacountyor.gov/departments/elections',
 'Coos':      'https://www.co.coos.or.us/departments/elections',
 'Crook':     'https://www.co.crook.or.us/departments/elections',
 'Curry':     'https://www.co.curry.or.us/departments/elections',
 'Deschutes': 'https://www.deschutes.org/elections',
 'Douglas':   'https://www.co.douglas.or.us/elections/index.asp',
 'Gilliam':   'https://www.co.gilliam.or.us/county_services/elections',
 'Grant':     'https://www.grantcountyor.gov/departments/elections',
 'Harney':    'https://www.co.harney.or.us/departments/elections',
 'Hood River':'https://hoodriver.or.gov/departments/elections',
 'Jackson':   'https://jcgov.us/elections',
 'Jefferson': 'https://jeffersoncountyor.gov/government/departments/elections/',
 'Josephine': 'https://www.co.josephine.or.us/elections',
 'Klamath':   'https://www.klamathcounty.org/divisions/county-clerk/elections',
 'Lake':      'https://www.co.lake.or.us/departments/elections',
 'Lane':      'https://www.lanecounty.org/departments/electionsvital_records',
 'Lincoln':   'https://www.co.lincoln.or.us/departments/elections',
 'Linn':      'https://www.co.linn.or.us/elections',
 'Malheur':   'https://malheurco.org/elections/',
 'Marion':    'https://www.co.marion.or.us/CO/elections/',
 'Morrow':    'https://www.co.morrow.or.us/departments/elections',
 'Multnomah': 'https://multco.us/elections',
 'Polk':      'https://www.co.polk.or.us/elections',
 'Sherman':   'https://www.co.sherman.or.us/county-departments/elections',
 'Tillamook': 'https://www.co.tillamook.or.us/elections',
 'Umatilla':  'https://www.umatillacounty.net/county-services/elections',
 'Union':     'https://www.union-county.org/departments/elections',
 'Wallowa':   'https://co.wallowa.or.us/departments/elections',
 'Wasco':     'https://www.co.wasco.or.us/elections',
 'Washington':'https://www.washingtoncountyoregon.gov/elections',
 'Wheeler':   'https://www.co.wheeler.or.us/departments/elections',
 'Yamhill':   'https://www.co.yamhill.or.us/elections',
}

UTILITY_URLS = {
 'Portland General Electric': 'https://www.portlandgeneral.com/',
 'Pacific Power': 'https://www.pacificpower.net/',
 'Tillamook PUD': 'https://www.tillamookpud.org/',
 'Central Lincoln PUD': 'https://www.clpud.org/',
 'EWEB': 'https://www.eweb.org/',
 'Douglas Electric Cooperative': 'https://www.douglas-electric.coop/',
 'Coos-Curry Electric Cooperative': 'https://www.cooscurry.com/',
 'Northern Wasco County PUD': 'https://www.nwcpud.com/',
 'Wasco Electric Cooperative': 'https://www.wascoelectric.com/',
 'Columbia Basin Electric Cooperative': 'https://www.columbiapowertrust.org/',
 'Umatilla Electric Cooperative': 'https://www.umatillaelectric.com/',
 'Oregon Trail Electric Cooperative': 'https://www.otec.coop/',
 'Harney Electric Cooperative': 'https://www.harneyelectric.com/',
 'Idaho Power': 'https://www.idahopower.com/',
 'Columbia Power Cooperative': 'https://www.colpow.com/',
 'Central Electric Cooperative': 'https://www.cepco.com/',
 'Pacific Power / Central Electric Cooperative': '',
 'NW Natural': 'https://www.nwnatural.com/',
 'Surprise Valley Electric': 'https://www.svec.org/',
}


def utility_links_html(electric_str):
    """'Pacific Power / EWEB' -> linked names joined by ' / ' (plain text when no URL is known)."""
    parts = []
    for name in [p.strip() for p in (electric_str or '').split('/') if p.strip()]:
        url = UTILITY_URLS.get(name)
        parts.append(f'<a href="{e(url)}" target="_blank" rel="noopener">{e(name)}</a>' if url else e(name))
    return ' / '.join(parts)


STATE_LINKS = [
 ('Oregon.gov', 'https://www.oregon.gov/'),
 ('Oregon DMV', 'https://www.oregon.gov/odot/dmv/'),
 ('WorkSource Oregon', 'https://www.worksourceoregon.org/'),
 ('Oregon Dept. of Education', 'https://www.oregon.gov/ode/'),
 ('Oregon Health Plan', 'https://one.oregon.gov/'),
 ('SNAP Food Benefits', 'https://www.oregon.gov/odhs/food/pages/snap.aspx'),
 ('Oregon Food Bank', 'https://www.oregonfoodbank.org/'),
 ('211info', 'https://www.211info.org/'),
 ('Oregon Housing', 'https://www.oregon.gov/ohcs/'),
 ('Travel Oregon', 'https://traveloregon.com/'),
]

# Maps the 15 internal sub-regions (from COUNTY_INFO) to 7 public-facing Oregon regions
BIG_REGION_MAP = {
 'Portland Metro':'Portland Metro','Northwest Oregon':'Portland Metro',
 'Willamette Valley':'Willamette Valley',
 'North Coast':'Oregon Coast','Central Coast':'Oregon Coast','South Coast':'Oregon Coast',
 'Columbia River Gorge':'Columbia River Gorge','North Central Oregon':'Columbia River Gorge',
 'Central Oregon':'Central Oregon',
 'Eastern Oregon':'Eastern Oregon','Northeast Oregon':'Eastern Oregon','Southeast Oregon':'Eastern Oregon',
 'Rogue Valley':'Southern Oregon','Southwest Oregon':'Southern Oregon','South Central Oregon':'Southern Oregon',
}

REGION_SLUGS = {
 'Portland Metro':'portland-metro','Willamette Valley':'willamette-valley',
 'Oregon Coast':'oregon-coast','Columbia River Gorge':'columbia-river-gorge',
 'Central Oregon':'central-oregon','Eastern Oregon':'eastern-oregon','Southern Oregon':'southern-oregon',
}

REGION_COUNTIES = {
 'Portland Metro':['Multnomah','Washington','Clackamas','Columbia'],
 'Willamette Valley':['Yamhill','Marion','Polk','Linn','Benton','Lane'],
 'Oregon Coast':['Clatsop','Tillamook','Lincoln','Coos','Curry'],
 'Columbia River Gorge':['Hood River','Wasco','Sherman','Gilliam','Morrow','Wheeler'],
 'Central Oregon':['Deschutes','Jefferson','Crook'],
 'Eastern Oregon':['Umatilla','Union','Wallowa','Baker','Grant','Harney','Malheur'],
 'Southern Oregon':['Josephine','Jackson','Douglas','Klamath','Lake'],
}

REGION_CONTENT = {
 'Portland Metro':{
  'desc':"Oregon's largest metropolitan area, home to Portland, Beaverton, Hillsboro, Gresham, and Lake Oswego. Tech industry, world-class food scene, and easy access to mountains and coast.",
  'hero_sub':"Oregon's largest city and surrounding metro \u2014 tech, food, arts, and outdoor access all within reach.",
  'living':"The Portland Metro area offers the most urban amenities in Oregon: a robust public transit system (TriMet MAX light rail, buses, WES commuter rail), internationally recognized restaurants, a vibrant arts scene, and major employers in technology (Intel, Nike, Adidas, Oregon Health \u0026 Science University). Housing costs are higher than rural Oregon but moderate compared to Seattle or San Francisco. Neighborhoods range from dense urban core to quiet suburban communities in Washington County's Silicon Forest.",
  'visiting':"Visitors come for Powell's Books (one of the world's largest independent bookstores), the International Rose Test Garden, Portland Saturday Market, food carts, and year-round farmers markets. Day trips reach Mt. Hood (45 min), the Columbia River Gorge (30 min), Oregon Coast (90 min), and Willamette Valley wine country (30\u201360 min south).",
  'highlights':["Portland \u2014 the Rose City, Oregon's largest city, food and craft beer capital","Beaverton \u0026 Hillsboro \u2014 Intel and Nike campuses, Silicon Forest tech corridor","Lake Oswego \u2014 upscale lakeside community, easy MAX access to Portland","Gresham \u2014 eastern metro gateway, affordable alternative to Portland","Forest Grove \u2014 Pacific University, edge of Willamette Valley wine country","St. Helens \u2014 Columbia River setting, historic main street, \u201cHalloween Town\u201d filming location"],
 },
 'Willamette Valley':{
  'desc':"Oregon's heartland stretching from Portland south to Eugene \u2014 wine country, university towns, fertile farmland, and the state capital Salem. Home to over half of Oregon's population.",
  'hero_sub':"Oregon wine country, university towns, and the state capital \u2014 the fertile heart of the state.",
  'living':"The Willamette Valley is where most Oregonians live. Salem offers state government jobs, healthcare (Salem Health, Kaiser), and a family-friendly pace. Eugene is a college town (University of Oregon) with a strong arts culture. Corvallis (Oregon State University) ranks highly for quality of life and walkability. The valley floor is agricultural \u2014 wine grapes, berries, hazelnuts, Christmas trees \u2014 and housing remains relatively affordable compared to Portland. Each major city has local transit; the Valley Connector bus links many communities.",
  'visiting':"The valley is Oregon's premier wine destination, with more than 700 wineries producing world-class Pinot Noir. Oregon Garden (Silverton), Silver Falls State Park (\u201cTrail of Ten Falls\u201d), Oregon Country Fair in Veneta, whitewater rafting on the McKenzie River, and Crater Lake day trips from Eugene are all popular. The coast is 60\u201390 minutes west.",
  'highlights':["Salem \u2014 Oregon state capital, Willamette University, historic mission","Eugene \u2014 University of Oregon, Pre's Trail, world-class track \u0026 field","Corvallis \u2014 Oregon State University, walkable downtown, top quality of life","Albany \u2014 Victorian architecture, covered bridges, LBCC","McMinnville \u2014 wine country hub, Evergreen Aviation \u0026 Space Museum","Silverton \u2014 Silver Falls State Park gateway, Oregon Garden"],
 },
 'Oregon Coast':{
  'desc':"More than 360 miles of publicly owned Pacific coastline from Astoria south to Brookings. All Oregon beaches are free and open to everyone. Seafood, state parks, lighthouses, and dramatic headlands.",
  'hero_sub':"Over 360 miles of publicly accessible Pacific coastline \u2014 every beach belongs to everyone.",
  'living':"Coastal living means a mild marine climate (warm summers, wet winters), smaller tight-knit communities, and a tourism-driven economy. Newport and Coos Bay are the largest coast cities with more services. Housing is relatively affordable outside popular resort towns like Cannon Beach. Fishing, crabbing, and outdoor work are common livelihoods alongside hospitality and healthcare. Many coastal residents commute seasonally or work remotely.",
  'visiting':"Top stops include Cannon Beach's iconic Haystack Rock, the Oregon Coast Aquarium in Newport, Cape Perpetua Scenic Area near Yachats, Bandon's Face Rock Creamery and world-class golf, and Astoria with its column viewpoint and Goonies history. Whale-watching peaks in March/April and December. All state beaches are free and accessible year-round.",
  'highlights':["Astoria \u2014 Oregon's oldest settlement, Lewis \u0026 Clark history, Victorian homes","Cannon Beach \u2014 Haystack Rock, art galleries, fine dining","Newport \u2014 Oregon Coast Aquarium, historic Bayfront, Hatfield Marine Science Center","Florence \u2014 Sea Lion Caves, Oregon Dunes National Recreation Area","Bandon \u2014 Face Rock Creamery, Bandon Dunes Golf Resort","Brookings \u2014 Azalea Festival, Harbor, near California Redwood forests"],
 },
 'Columbia River Gorge':{
  'desc':"A National Scenic Area carved by the Columbia River on the Oregon\u2013Washington border. Hood River is the outdoor hub; the area is famous for windsurfing, waterfalls, fruit orchards, and dramatic canyon views.",
  'hero_sub':"Waterfalls, windsurfing, and orchard country \u2014 a spectacular river canyon on the Oregon\u2013Washington border.",
  'living':"Hood River is the main population center \u2014 a lively small city with a strong outdoor and craft-beverage culture and views of Mt. Adams and Mt. Hood. The Dalles is a historic trading post and growing tech hub (Google data center) with more affordable housing. East of the Cascades, Sherman, Gilliam, Morrow, and Wheeler counties are sparsely populated wheat-farming and ranching communities with very low costs of living.",
  'visiting':"The Historic Columbia River Highway offers spectacular driving with multiple waterfall pullouts. Multnomah Falls (Oregon's tallest, 620 ft) draws over 2 million visitors annually. Hood River is the world capital of kiteboarding and windsurfing, with Mt. Hood skiing an hour south. The Fruit Loop driving tour passes apple, pear, and cherry orchards in spring bloom. Maupin is the hub for Deschutes River whitewater rafting.",
  'highlights':["Hood River \u2014 kiteboarding/windsurfing mecca, fruit orchards, craft breweries","The Dalles \u2014 historic Columbia River port, murals, growing tech presence","Cascade Locks \u2014 Bridge of the Gods, Pacific Crest Trail crossing, sternwheeler tours","Maupin \u2014 Deschutes River whitewater rafting and fly fishing","Fossil \u2014 John Day Fossil Beds gateway, leaf impressions in Wheeler County rock","Condon \u2014 wheat farming community, star-gazing in Gilliam County dark skies"],
 },
 'Central Oregon':{
  'desc':"High desert east of the Cascades centered on Bend, Oregon's fastest-growing city. World-class skiing, mountain biking, rock climbing, fly fishing, and more sunny days than anywhere else in the state.",
  'hero_sub':"High desert sunshine, volcanic landscapes, and outdoor adventure \u2014 anchored by the city of Bend.",
  'living':"Bend has grown rapidly and now offers urban amenities \u2014 craft breweries, restaurants, a downtown arts scene, St. Charles Health System \u2014 in a high-desert outdoor recreation setting. Housing prices have risen significantly due to in-migration. Redmond is more affordable and growing quickly. Madras and Prineville offer smaller-town rural life with lower costs. The region averages over 300 sunny days per year and receives far less rainfall than western Oregon.",
  'visiting':"Mt. Bachelor ski resort is one of the West's largest, with skiing into late spring. The Deschutes River Trail and Phil's Trail network draw mountain bikers from across the country. Smith Rock State Park is a world-class rock climbing and sport-climbing destination with dramatic spire views. The High Desert Museum, Lava Lands Visitor Center, and Newberry Volcanic National Monument fill out an active itinerary.",
  'highlights':["Bend \u2014 outdoor recreation hub, craft brewery capital, Old Mill District","Redmond \u2014 more affordable Bend neighbor, Redmond Airport regional hub","Madras \u2014 gateway to Smith Rock, total solar eclipse 2017 ground zero","Prineville \u2014 Les Schwab Tires headquarters, Ochoco Mountains access","Sisters \u2014 western-themed charming small town, Three Sisters wilderness gateway","Mt. Bachelor \u0026 Smith Rock \u2014 skiing and climbing icons of the high desert"],
 },
 'Eastern Oregon':{
  'desc':"Oregon's vast interior \u2014 ranching, frontier history, the Wallowa Mountains (Oregon's Alps), Steens Mountain, the Painted Hills, and some of the darkest skies in the lower 48. Half of Oregon's land, a fraction of its people.",
  'hero_sub':"Wide-open high desert, the Wallowa Mountains, wild rivers, and frontier towns \u2014 Oregon's big-sky country.",
  'living':"Eastern Oregon offers some of the most affordable housing in the state, wide open spaces, and a ranching and agricultural economy. Pendleton is the largest city and a regional hub with healthcare services (CHI St. Anthony). La Grande (Eastern Oregon University) and Baker City (remarkably preserved Victorian downtown) are appealing smaller cities. Ontario serves as a regional commercial center on the Idaho border. Remote communities may have limited healthcare access. Most of Eastern Oregon observes Pacific Time, but Malheur County observes Mountain Time.",
  'visiting':"The Wallowa Mountains and Eagle Cap Wilderness offer world-class backpacking, horse packing, and skiing at Ferguson Ridge. Steens Mountain (9,773 ft) rises abruptly from the Alvord Desert playa \u2014 one of Oregon's most dramatic landscapes. The Painted Hills unit of John Day Fossil Beds offers vivid red-and-gold striped hillsides. Pendleton Round-Up (September) is one of the West's largest rodeos. The Oregon Trail Historic Route runs the length of the region.",
  'highlights':["Pendleton \u2014 Pendleton Round-Up rodeo, woolen mills, underground historical tours","La Grande \u2014 Eastern Oregon University, Blue Mountains gateway","Baker City \u2014 National Historic Oregon Trail Interpretive Center, Victorian architecture","Enterprise \u0026 Joseph \u2014 gateway to the Wallowa Mountains and Eagle Cap Wilderness","Burns \u2014 gateway to Steens Mountain and Malheur National Wildlife Refuge","Mitchell \u2014 Painted Hills gateway, fossil beds, world-class dark-sky viewing"],
 },
 'Southern Oregon':{
  'desc':"Medford, Ashland, Grants Pass, and Roseburg anchor a region of mild climate, wine country, the Oregon Shakespeare Festival, Crater Lake, and the wild Rogue River. Warmer and sunnier than western Oregon.",
  'hero_sub':"Wine, Shakespeare, Crater Lake, and the Rogue River \u2014 Oregon's sun-drenched southern corner.",
  'living':"Southern Oregon attracts retirees and remote workers for its mild climate (the Medford-Ashland area gets considerably more sun than Portland), relatively affordable housing, and access to outdoor recreation. Medford is the regional healthcare hub (Asante Rogue Regional, Providence Medford). The Umpqua Valley around Roseburg is emerging wine country with lower land prices. Klamath Falls is an agricultural and outdoor recreation center with some of the state's most affordable housing. Douglas County's coastal-adjacent communities offer rural living near the Umpqua River.",
  'visiting':"Crater Lake National Park \u2014 the deepest lake in the US at 1,943 feet and with famously vivid blue water \u2014 is Southern Oregon's iconic destination. The Oregon Shakespeare Festival in Ashland runs from February to October. Rafting and jetboat excursions on the wild and scenic Rogue River, Wildlife Images Rehabilitation Center in Grants Pass, Wildlife Safari drive-through park in Winston, and Applegate Valley and Umpqua Valley winery trails round out the region.",
  'highlights':["Medford \u2014 regional hub, Pear Blossom Festival, Bear Creek Greenway","Ashland \u2014 Oregon Shakespeare Festival, Lithia Park, charming downtown","Grants Pass \u2014 Rogue River, Hellgate Jetboat Excursions, Riverside Park","Roseburg \u2014 Umpqua Valley wine trail, Wildlife Safari drive-through zoo","Klamath Falls \u2014 Crater Lake gateway, OIT campus, affordable high-desert living","Jacksonville \u2014 entire town is a National Historic Landmark, Britt Festivals"],
 },
}

# Unique hero taglines (key = city slug). Cities not listed get an auto-generated tagline.
CITY_TAGLINES = {
    "portland": "The Rose City — Oregon's largest city, vibrant food scene & outdoor gateway",
    "salem": "Oregon's Capital City — nestled in the heart of the Willamette Valley wine country",
    "eugene": "Track Town USA — home of the University of Oregon and a thriving arts scene",
    "bend": "High Desert Adventure Hub — sunny skies, craft beer, and outdoor recreation",
    "medford": "Southern Oregon's Hub — gateway to Crater Lake, Rogue Valley wines & outdoor adventure",
    "gresham": "Gateway to the Columbia River Gorge — Mount Hood's neighbor in the Portland Metro",
    "hillsboro": "Oregon's Silicon Forest — technology industry hub in the Tualatin Valley",
    "beaverton": "Nike's Hometown — a vibrant tech corridor in Washington County",
    "corvallis": "Home of Oregon State University — college town on the Willamette River",
    "springfield": "Gateway to the McKenzie River — Lane County's river city at the foot of the Cascades",
    "lake-oswego": "Oregon's 'Lake Town' — upscale lakefront living near Portland",
    "albany": "The Rare Metals Capital — Victorian homes, covered bridges and Willamette Valley farmland",
    "astoria": "Oregon's Oldest American Settlement — where Lewis & Clark met the Pacific",
    "cannon-beach": "Home of Haystack Rock — iconic Oregon Coast arts and nature destination",
    "newport": "Dungeness Crab Capital of Oregon — marine science hub on the Central Coast",
    "ashland": "Oregon Shakespeare Festival City — cultural gem in the Siskiyou Mountains",
    "sisters": "Gateway to Three Sisters Wilderness — charming Western-themed mountain town",
    "hood-river": "Windsurfing Capital of the World — orchard country in the Columbia River Gorge",
    "tillamook": "Oregon's Cheese Capital — dairy country on the spectacular North Coast",
    "seaside": "Oregon's Largest Beach Resort Town — family fun on the North Coast",
    "lincoln-city": "Oregon's Kite Country — glass float hunting and Central Coast beaches",
    "florence": "Gateway to the Oregon Dunes — charming harbor town on the Central Coast",
    "coos-bay": "Oregon's Largest Bay City — gateway to Cape Arago and South Coast adventures",
    "grants-pass": "Whitewater Rafting Capital — Rogue River adventures in Southern Oregon",
    "klamath-falls": "Upper Klamath Country — birding paradise and gateway to Crater Lake",
    "la-grande": "Blue Mountains Gateway — home of Eastern Oregon University in the Grande Ronde Valley",
    "ontario": "Eastern Oregon's Agricultural Hub — on the Idaho border in the Snake River Valley",
    "pendleton": "Home of the Pendleton Round-Up — Eastern Oregon's rodeo and wool capital",
    "the-dalles": "Gateway to the Columbia River Gorge — historic Lewis & Clark encampment site",
    "mcminnville": "Willamette Valley Wine Country Hub — gateway to Oregon's Pinot Noir region",
    "newberg": "Herbert Hoover's Boyhood Home — heart of Chehalem Mountains wine country",
    "cottage-grove": "Covered Bridge Capital of Oregon — Row River trails and historic charm",
    "brookings": "Oregon's Banana Belt — the warmest and sunniest city on the Oregon Coast",
    "gold-beach": "Jet Boat Capital of Oregon — where the Rogue River meets the Pacific",
    "bandon": "Oregon's Cranberry Capital — world-class golf and wildlife on the South Coast",
    "waldport": "Alsea Bay Bridge Town — gateway to pristine Central Oregon Coast beaches",
    "yachats": "The Gem of the Oregon Coast — dramatic tidepools and rugged Pacific shoreline",
    "depoe-bay": "The World's Smallest Harbor — whale watching capital of the Oregon Coast",
    "rockaway-beach": "A Serene Stretch of Oregon's North Coast — family beach town escape",
    "manzanita": "Oregon's Quietest Beach Town — artsy hideaway on Nehalem Bay",
    "wheeler": "Nestled on Nehalem Bay — a peaceful escape on the Oregon North Coast",
    "bay-city": "Small-Town Charm on Tillamook Bay — Oregon North Coast fishing community",
    "garibaldi": "Oregon's Deep-Sea Fishing Port — gateway to Tillamook Bay",
    "warrenton": "Gateway to Fort Stevens — where the Columbia River meets the Pacific",
    "st-helens": "Named for Mount St. Helens — filming location for 'Halloweentown'",
    "tualatin": "The Turtle City — fast-growing suburb south of Portland",
    "wilsonville": "Oregon's I-5 Crossroads — Willamette Valley growth hub south of Portland",
    "west-linn": "City of Hills and Rivers — scenic living where the Tualatin meets the Willamette",
    "oregon-city": "End of the Oregon Trail — the first incorporated city west of the Rockies",
    "gladstone": "Where the Clackamas Meets the Willamette — scenic Portland Metro suburb",
    "happy-valley": "One of Oregon's Fastest-Growing Cities — scenic foothills living in Clackamas County",
    "troutdale": "Gateway to the Columbia River Gorge — historic Sandy River town",
    "wood-village": "A Small City with Big Community Spirit — east Portland Metro suburb",
    "fairview": "A Friendly East Portland Metro Community — near Blue Lake Regional Park",
    "maywood-park": "One of Oregon's Smallest Cities — a tight-knit Portland enclave",
    "king-city": "A Planned Retirement Community — south of Beaverton in Washington County",
    "durham": "One of Oregon's Smallest Cities — peaceful Tualatin River community",
    "sherwood": "Robin Hood's Oregon Town — rapidly growing Washington County suburb",
    "tigard": "Washington County's Growth Hub — Fanno Creek trails and Portland access",
    "cornelius": "Washington County's Agricultural Heritage — Tualatin Valley farming community",
    "forest-grove": "Home of Pacific University — trees, trails and history west of Portland",
    "banks": "Gateway to Tillamook State Forest — outdoor recreation in Washington County",
    "north-plains": "Pumpkin Patch Country of Washington County — family farms near Portland",
    "st-paul": "Home of the St. Paul Rodeo — historic French Prairie farming community",
    "donald": "Small-Town Heart of the Willamette Valley — historic farming community in Marion County",
    "mount-angel": "Oregon's Bavarian Town — host of the annual Oktoberfest celebration",
    "silverton": "Oregon Garden City — home of the Oregon Garden and gateway to Silver Falls",
    "stayton": "Gateway to the North Santiam Canyon — Santiam River valley community",
    "sublimity": "Gateway to Silver Falls — peaceful Marion County farming community",
    "turner": "Small-Town Marion County Charm — gateway to Salem via scenic farmland",
    "detroit": "Gateway to Detroit Lake — North Santiam Canyon mountain recreation hub",
    "gates": "Tiny Mountain Gateway — North Santiam Canyon scenic corridor",
    "mill-city": "The Little Town with Big Scenery — North Santiam River canyon community",
    "independence": "Oregon's Historic Hop Capital — Willamette River town in Polk County",
    "monmouth": "Home of Western Oregon University — liberal arts college town in Polk County",
    "dallas": "Polk County's Agricultural Center — gateway to the Coast Range",
    "falls-city": "Little Luckiamute River Town — tiny Polk County community near the Coast Range",
    "toledo": "Lincoln County's Historic Mill Town — on the Yaquina River",
    "reedsport": "Gateway to the Oregon Dunes National Recreation Area — Umpqua River town",
    "north-bend": "Oregon's Bay Area Twin City — gateway to the South Coast",
    "port-orford": "Oldest Town Site on the Oregon Coast — dramatic coastal bluffs and fishing port",
    "cave-junction": "Gateway to Oregon Caves — Illinois Valley hub in the Siskiyou Mountains",
    "jacksonville": "A National Historic Landmark Town — Gold Rush-era gem near Medford",
    "talent": "Rogue Valley's Artisan Hub — farm-to-table dining and arts near Ashland",
    "phoenix": "Rogue Valley's Growing Community — between Medford and Talent",
    "central-point": "Gateway to Table Rocks — Rogue Valley's Crater Lake Cheese hometown",
    "eagle-point": "Rogue River Valley Gateway — small-town charm near Medford",
    "shady-cove": "Rogue River Recreation Town — fishing, rafting and relaxing in Jackson County",
    "butte-falls": "A Tiny Mountain Town in Jackson County — gateway to Rogue River headwaters",
    "roseburg": "Timber Capital of the Nation — gateway to Umpqua Valley wine country",
    "sutherlin": "Junction City of Douglas County — North Umpqua Valley crossroads",
    "myrtle-creek": "On the South Umpqua — myrtlewood crafts and small-town Douglas County charm",
    "canyonville": "Gateway to Seven Feathers — historic stagecoach stop in Douglas County",
    "riddle": "Oregon's Nickel Mining Heritage — tiny Douglas County community",
    "winston": "Wildlife Safari Hometown — Douglas County's hidden gem",
    "drain": "Historic Railroad Town in Douglas County — gateway to the Coast Range",
    "creswell": "Willamette Valley's Growth Town — Eugene-Springfield Metro gateway",
    "oakridge": "Mountain Biking Capital of the Pacific Northwest — Willamette National Forest hub",
    "lowell": "Fall Creek Country — gateway to Dexter and Lookout Point reservoirs",
    "veneta": "Fern Ridge Lake Community — home of the legendary Oregon Country Fair",
    "junction-city": "Oregon's Danish Heritage Town — Willamette Valley agricultural crossroads",
    "coburg": "Antique Capital of the Willamette Valley — tiny historic city near Eugene",
    "harrisburg": "Willamette River Farming Town — grass seed country in Linn County",
    "halsey": "Linn County's Agricultural Heart — grass seed farming community",
    "brownsville": "Historic Wool Town in the Calapooia River Valley — Linn County charm",
    "lebanon": "Strawberry Capital of Oregon — Linn County's growing Santiam River city",
    "sweet-home": "Gateway to the Cascades — fishing, hiking and reservoir recreation near Albany",
    "idanha": "North Santiam Canyon Gateway — tiny mountain community",
    "lyons": "Mill Town on the North Santiam — gateway to Detroit Lake",
    "scio": "Covered Bridge Town in Linn County — small farming community near Albany",
    "tangent": "Oregon's Grass Seed Capital — Willamette Valley agricultural community",
    "sodaville": "Mineral Springs Heritage Town — tiny Linn County farming community",
    "philomath": "Home of Marys Peak — Benton County's gateway to the Coast Range",
    "adair-village": "A Small Planned Community — former military base in Benton County",
    "monroe": "Southern Benton County Farm Town — Willamette Valley agricultural heritage",
    "hermiston": "Watermelon Capital of Oregon — Eastern Oregon's agricultural hub",
    "enterprise": "Wallowa County Seat — gateway to the Eagle Cap Wilderness and Hells Canyon",
    "joseph": "Bronze Sculpture Capital — gateway to Wallowa Lake and the Eagle Cap Wilderness",
    "lostine": "Tiny Wallowa Valley Town — gateway to the Eagle Cap Wilderness",
    "wallowa": "Wallowa Valley Agricultural Town — small community near the Eagle Cap",
    "nyssa": "Treasure Valley's Onion Country — Eastern Oregon's agricultural crossroads",
    "vale": "Snake River Valley Heritage Town — Malheur County seat on the Oregon Trail",
    "burns": "High Desert Cattle Country — gateway to Malheur National Wildlife Refuge",
    "hines": "Twin City to Burns — gateway to Harney Basin birding and ranching",
    "john-day": "Oregon's Gold Mining Legacy Town — gateway to the John Day Fossil Beds",
    "prairie-city": "Grant County Mountain Town — gateway to Strawberry Mountain Wilderness",
    "canyon-city": "Grant County's Historic Gold Rush Town — near John Day Fossil Beds",
    "fossil": "Wheeler County Seat — heart of the John Day Country fossil region",
    "condon": "Gilliam County's Wheat Country Town — Eastern Oregon agricultural community",
    "arlington": "Columbia River Town — gateway to Eastern Oregon wheat country",
    "boardman": "Columbia River Gateway — Eastern Oregon's growing agricultural hub",
    "umatilla": "Columbia River Crossing — gateway to the Umatilla National Forest",
    "echo": "Historic Oregon Trail Town — Umatilla River community in Umatilla County",
    "stanfield": "Umatilla County Agricultural Town — near the Columbia River Basin",
    "irrigon": "Columbia Basin Irrigation Town — gateway to Lake Umatilla recreation",
    "lakeview": "Tallest Town in Oregon — hang gliding hub and gateway to Hart Mountain",
    "paisley": "Summer Lake Basin Ranching Town — one of Lake County's most remote communities",
    "chiloquin": "Upper Klamath Country — gateway to Collier Memorial State Park",
    "bonanza": "Klamath Basin Town — Klamath County agricultural community",
    "malin": "Potato Capital of Klamath County — irrigated basin agricultural community",
    "merrill": "Klamath Basin Farming Town — near Lower Klamath National Wildlife Refuge",
    "redmond": "Central Oregon's Crossroads — airport hub and outdoor recreation near Bend",
    "prineville": "Oregon's Cowboy Town — Crook County's gateway to Prineville Reservoir",
    "madras": "Solar Eclipse Capital of Oregon — gateway to Lake Billy Chinook and Warm Springs",
    "metolius": "Tiny Jefferson County Town — gateway to the Cascade Mountains",
    "culver": "Jefferson County's Agricultural Hub — near Cove Palisades State Park",
    "maupin": "Whitewater Rafting Capital of the Deschutes River — gateway to the Lower Deschutes",
    "antelope": "Rajneeshee History Town — tiny Wasco County community",
    "spray": "North Fork John Day River Town — tiny Wheeler County community",
    "mitchell": "The Painted Hills Gateway — tiny Wheeler County community",
    "baker-city": "Oregon's 'Queen City of the Mines' — gold rush heritage in Eastern Oregon",
    "halfway": "Gateway to Hells Canyon — Baker County's remote ranching community",
    "richland": "Eagle Valley Ranching Town — Baker County gateway to Hells Canyon",
    "unity": "Upper Burnt River Valley — tiny Baker County mountain community",
    "heppner": "Morrow County Seat — Eastern Oregon wheat farming community",
    "ione": "Columbia Plateau Farming Town — tiny Morrow County community",
    "lexington": "Morrow County's Tiny Farming Community — Eastern Oregon wheat country",
}

# Per-region hero theme: gradient + short evocative line
REGION_THEME = {
    'Portland Metro': ('#2b2d42', '#4a4e69', 'City lights, bridges and forested hills where the Willamette meets the Columbia.'),
    'Willamette Valley': ('#1b4332', '#40916c', 'Rolling vineyards, covered bridges and river towns in Oregon\u2019s green heart.'),
    'Oregon Coast': ('#073b4c', '#0a9396', 'Sea stacks, lighthouses and misty headlands along 363 miles of public shoreline.'),
    'Columbia River Gorge': ('#0b2545', '#1d4e89', 'Basalt cliffs, roaring waterfalls and wind-swept river canyons.'),
    'Central Oregon': ('#1d3557', '#2a9d8f', 'Snow-capped Cascades, ponderosa pine and endless high-desert sunshine.'),
    'Eastern Oregon': ('#7f4f24', '#b6862c', 'Big skies, rimrock canyons and frontier towns across Oregon\u2019s wide-open interior.'),
    'Southern Oregon': ('#6b4e16', '#386641', 'Sunlit valleys, wild rivers and the impossible blue of Crater Lake.'),
}

OREGON_FACTS = [
 ('Statehood','February 14, 1859 (33rd state admitted to the Union)'),
 ('Capital','<a href="/cities/salem/index.html">Salem</a>'),
 ('Largest city','<a href="/cities/portland/index.html">Portland</a>'),
 ('Population (2020 Census)','4,237,256 (27th most populous state)'),
 ('Area','98,379 sq mi (9th largest state)'),
 ('Coastline','363 miles of publicly owned Pacific beaches'),
 ('Counties','36 (see <a href="/counties/index.html">all counties</a>)'),
 ('Incorporated cities','241 (see <a href="/cities/index.html">all cities A\u2013Z</a>)'),
 ('Geographic regions','7 (see <a href="/regions/index.html">all regions</a>)'),
 ('Nickname','The Beaver State'),
 ('Motto','<em>Alis Volat Propriis</em> (\u201cShe flies with her own wings\u201d)'),
 ('State bird','Western Meadowlark'),
 ('State flower','Oregon Grape'),
 ('State tree','Douglas Fir'),
 ('State animal','American Beaver'),
 ('State fish','Chinook Salmon'),
 ('State song','\u201cOregon, My Oregon\u201d (adopted 1927)'),
 ('Highest point','Mt. Hood, 11,249 ft (3,429 m)'),
 ('Longest river','Columbia River (forms the northern border with Washington)'),
 ('Time zone','Pacific Time (most of state); Mountain Time (Malheur County)'),
 ('Abbreviation','OR (postal); Ore. (traditional)'),
 ('No sales tax','Oregon levies no statewide sales tax'),
]

CSS = ":root{--gd:#14382a;--g:#1a5632;--gold:#c8a24b;--blue:#1f4e79;--bg:#f6f8f7;--tx:#22302b;--mu:#5c6b64}*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Inter',system-ui,sans-serif;color:var(--tx);line-height:1.6;background:#fff}h1,h2,h3{font-family:Georgia,serif;line-height:1.25}.wrap{max-width:1000px;margin:0 auto;padding:0 24px}.hd{background:var(--gd);color:#fff;padding:14px 0;position:sticky;top:0;z-index:50}.hd nav{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}.logo{display:flex;align-items:center;gap:10px;font-weight:800;font-size:1.1rem;color:#fff;text-decoration:none}.badge{width:30px;height:30px;background:var(--gold);border-radius:50%;display:flex;align-items:center;justify-content:center}.nl{list-style:none;display:flex;gap:16px;flex-wrap:wrap}.nl a{color:#dbe7e0;text-decoration:none;font-weight:600;font-size:.9rem}.nl a:hover{color:var(--gold)}.hero{background:linear-gradient(160deg,var(--gd),var(--g));color:#fff;padding:52px 0 44px;margin-bottom:36px}.hero h1{font-size:clamp(1.6rem,4vw,2.4rem);max-width:760px}.hero p{color:#dceee3;margin-top:12px;max-width:640px}.crumbs{font-size:.88rem;color:var(--mu);padding:14px 0 0}.crumbs a{color:var(--blue);text-decoration:none}h2.st{font-size:1.45rem;color:var(--gd);margin:36px 0 16px;border-bottom:3px solid var(--g);padding-bottom:8px}.facts{background:var(--bg);border:1px solid #e3eae6;border-radius:10px;padding:20px;margin:24px 0}.facts table{width:100%;border-collapse:collapse}.facts th{text-align:left;padding:9px;color:var(--gd);border-bottom:2px solid var(--g);width:35%;vertical-align:top}.facts td{padding:9px;border-bottom:1px solid #e3eae6}.facts a,.prose a,.tbl a{color:var(--blue)}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin:24px 0}.card{background:#fff;border:1px solid #e3eae6;border-top:4px solid var(--g);border-radius:10px;padding:20px}.card h3{font-size:1rem;color:var(--gd);margin-bottom:10px}.card ul{list-style:none}.card li{padding:6px 0;border-bottom:1px dashed #e3eae6;font-size:.92rem}.card a{color:var(--blue);text-decoration:none;font-weight:600}.faq details{background:#fff;border:1px solid #e3eae6;border-radius:8px;margin:9px 0;padding:0 16px}.faq summary{cursor:pointer;font-weight:600;padding:13px 0;color:var(--gd)}.faq p{padding:0 0 14px;font-size:.94rem}.faq ul{padding-left:20px}.faq li{padding:3px 0}.faq a{color:var(--blue)}.back{margin-top:40px;padding-top:18px;border-top:1px solid #e3eae6}.back a{color:var(--g);font-weight:700;text-decoration:none}.ft{background:var(--gd);color:#cfe0d6;padding:30px 0;text-align:center;font-size:.84rem;margin-top:44px}.ft a{color:#fff;text-decoration:none;font-weight:600}.ft .fl{margin-bottom:10px}.ft .fl a{margin:0 9px}.dir-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin:16px 0 26px}.dir-list a{background:var(--bg);border:1px solid #d7e2db;border-radius:6px;padding:10px 14px;text-decoration:none;color:var(--blue);font-weight:600;font-size:.9rem}.dir-list a small{display:block;color:var(--mu);font-weight:400;font-size:.78rem}.dir-list a:hover{background:var(--g);color:#fff}.dir-list a:hover small{color:#dceee3}.photo{margin:24px 0}.photo img{width:100%;max-height:440px;object-fit:cover;border-radius:10px;background:var(--bg)}.photo figcaption,.src{font-size:.8rem;color:var(--mu);margin-top:6px}.src a{color:var(--mu)}.prose p{margin:0 0 14px}.tbl{width:100%;border-collapse:collapse;margin:16px 0;font-size:.93rem}.tbl th{background:var(--gd);color:#fff;text-align:left;padding:9px}.tbl td{padding:9px;border-bottom:1px solid #e3eae6}.tbl tr:nth-child(even) td{background:var(--bg)}.alpha{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 20px}.alpha a{background:var(--gd);color:#fff;text-decoration:none;font-weight:700;padding:6px 11px;border-radius:5px}.alpha a:hover{background:var(--gold)}h3.letter{font-size:1.3rem;color:var(--gd);margin-top:22px;scroll-margin-top:80px}#q{width:100%;padding:12px 14px;font-size:1rem;border:2px solid #d7e2db;border-radius:8px}.gallery{display:grid;gap:14px;margin:20px 0 10px;grid-template-columns:repeat(auto-fill,minmax(260px,1fr))}.gallery.g1{display:flex}.gallery.g1 figure{width:fit-content;max-width:min(100%,560px)}.gallery figure{background:var(--bg);border:1px solid #e3eae6;border-radius:10px;overflow:hidden}.gallery img{width:100%;height:210px;object-fit:cover;display:block}.gallery.g1 img{width:auto;max-width:100%;height:auto;max-height:480px}.gallery figcaption{font-size:.82rem;color:var(--tx);padding:8px 10px;line-height:1.35}.gallery figcaption small{color:var(--mu);font-size:.74rem}.gallery figcaption a{color:var(--mu)}"

CSS += (
 # cards, headings, tables, hero
 ".hero{padding:64px 0 52px}.card{transition:all .2s}.card:hover{box-shadow:0 4px 16px rgba(0,0,0,.12);transform:translateY(-2px)}"
 ".card ul li:last-child{border-bottom:none}.card li small{display:block;color:var(--mu);font-weight:400;font-size:.82rem;line-height:1.4}"
 ".dir-list a{transition:all .2s}.dir-list a:hover{background:var(--g);color:#fff;transform:translateY(-1px)}"
 "h2.st{position:relative;padding-left:14px}h2.st:before{content:'';position:absolute;left:0;top:2px;bottom:10px;width:5px;border-radius:3px;background:var(--gold)}"
 ".facts tr:nth-child(even) th,.facts tr:nth-child(even) td{background:#eef3f0}"
 # hero variants: city / region / Oregon state
 ".city-hero,.region-hero{position:relative;overflow:hidden}.city-hero .wrap,.region-hero .wrap,.or-hero .wrap{position:relative;z-index:2}"
 ".hero p.city-tagline{font-family:Georgia,serif;font-style:italic;font-size:clamp(1.05rem,2.2vw,1.3rem);color:#f3e2b3;margin-top:10px;max-width:720px}"
 ".region-hero .hero-sub{color:#dceee3}"
 ".pills{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}.pill{display:inline-block;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.3);color:#fff;"
 "padding:5px 13px;border-radius:999px;font-size:.84rem;font-weight:600;backdrop-filter:blur(2px)}.pill a{color:#fff}"
 ".or-sil{position:absolute;right:3%;top:50%;transform:translateY(-50%);width:340px;max-width:45%;height:auto;opacity:.5;z-index:1;pointer-events:none}"
 ".or-hero{position:relative;overflow:hidden;min-height:420px;display:flex;align-items:center;color:#fff;margin-bottom:36px;padding:72px 0 64px;"
 "background:radial-gradient(ellipse at 75% 30%,rgba(200,162,75,.35),transparent 55%),linear-gradient(135deg,#0b2418 0%,#14382a 40%,#1f4e79 100%)}"
 ".or-hero .wrap{width:100%}.or-sil-lg{width:440px;max-width:42%;right:4%;opacity:.6}"
 ".or-hero h1{font-size:clamp(2rem,5.5vw,3.4rem);max-width:720px;text-shadow:0 2px 12px rgba(0,0,0,.35)}"
 ".or-eyebrow{text-transform:uppercase;letter-spacing:.18em;font-size:.8rem;font-weight:700;color:var(--gold);margin-bottom:14px}"
 ".or-sub{color:#dceee3;font-size:clamp(1rem,2vw,1.18rem);margin-top:16px;max-width:620px}"
 ".or-cta{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px}"
 ".btn-cta,.btn-ghost{display:inline-block;padding:12px 24px;border-radius:8px;font-weight:700;text-decoration:none;transition:all .2s}"
 ".btn-cta{background:var(--gold);color:#14382a}.btn-cta:hover{background:#e0bb5e;transform:translateY(-2px)}"
 ".btn-ghost{border:2px solid rgba(255,255,255,.7);color:#fff}.btn-ghost:hover{background:rgba(255,255,255,.12);border-color:#fff}"
 "@media(max-width:700px){.or-sil{opacity:.2;max-width:80%;right:-20px}.or-hero{min-height:360px}}"
 # quick facts + map
 ".qf{display:flex;gap:20px;align-items:flex-start;margin:24px 0}.qf .facts{flex:1;min-width:0;margin:0}"
 ".ormap{flex:0 0 216px;background:var(--bg);border:1px solid #e3eae6;border-radius:10px;padding:8px;text-align:center}"
 ".ormap svg{display:block;width:200px;height:160px}.ormap figcaption{font-size:.8rem;color:var(--mu);margin-top:4px}"
 # ticker (pure CSS)
 ".ticker{background:var(--gd);border-top:1px solid #2c5a45;border-bottom:1px solid #0b241a;overflow:hidden;white-space:nowrap;font-size:.85rem}"
 ".ticker-track{display:inline-block;padding:7px 0;animation:scroll-left 1500s linear infinite;will-change:transform}"
 ".ticker-track:hover{animation-play-state:paused}.ticker-track span{color:var(--gold);padding:0 26px;border-right:1px solid #2c5a45}"
 "@keyframes scroll-left{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}"
 "@media(prefers-reduced-motion:reduce){.ticker-track{animation-play-state:paused}}"
 # travel alerts banner
 "#alerts-bar{background:#fff8e6;border-bottom:1px solid #e8c873}#alerts-bar summary{max-width:1000px;margin:0 auto;padding:7px 24px;cursor:pointer;font-weight:700;font-size:.88rem;color:#7a4b00;list-style-position:inside}"
 "#alerts-bar summary:hover{color:#4f3100}#alerts-bar[open]{background:#fffbf0}#alerts-bar .ab{max-width:1000px;margin:0 auto;padding:4px 24px 16px;font-size:.9rem}"
 "#alerts-bar .ab-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}#alerts-bar .ab-grid div{background:#fff;border:1px solid #f0dca6;border-left:4px solid var(--g);border-radius:6px;padding:10px 12px}"
 "#alerts-bar .abh{display:block;color:var(--gd);font-size:.92rem;margin-bottom:4px}#alerts-bar a{color:var(--blue);font-weight:600}#alerts-bar ul{list-style:none}#alerts-bar li{padding:2px 0}"
 "#ab-live{margin-top:12px}#ab-live:empty{display:none}#ab-live p{margin:4px 0}#ab-live .ab-note{font-size:.78rem;color:var(--mu)}"
 # mobile
 "@media(max-width:600px){.cards{grid-template-columns:1fr}.hero{padding:40px 0 32px}.qf{flex-direction:column}.ormap{align-self:center}"
 ".wrap{padding:0 16px}.nl{gap:10px}.facts{padding:12px}.facts th{width:auto}.facts th,.facts td{display:block;border-bottom:none;padding:4px 6px}.facts td{border-bottom:1px solid #e3eae6;padding-bottom:9px}"
 "#alerts-bar summary,#alerts-bar .ab{padding-left:16px;padding-right:16px}}"
 # weather widget
 ".wx-card{background:#fff;border:1px solid #e3eae6;border-top:4px solid #1f4e79;border-radius:10px;padding:20px;margin:24px 0}"
 ".wx-card h3{font-size:1rem;color:var(--gd);margin-bottom:12px}"
 ".wx-loading{color:var(--mu);font-size:.9rem}"
 ".wx-cur{display:flex;flex-wrap:wrap;align-items:center;gap:14px;margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid #e3eae6}"
 ".wx-icon{font-size:2.6rem;line-height:1}.wx-temp{font-size:2rem;font-weight:700;color:var(--gd)}"
 ".wx-cond{font-size:1rem;color:var(--tx)}.wx-wind,.wx-humid{font-size:.88rem;color:var(--mu)}"
 ".wx-forecast{display:flex;gap:8px;flex-wrap:wrap}"
 ".wx-day{background:var(--bg);border:1px solid #e3eae6;border-radius:8px;padding:8px 10px;text-align:center;min-width:54px;flex:1}"
 ".wx-day-name{font-size:.78rem;font-weight:700;color:var(--gd)}.wx-day-icon{font-size:1.4rem;margin:4px 0}"
 ".wx-day-hi{font-size:.9rem;font-weight:700;color:var(--tx)}.wx-day-lo{font-size:.82rem;color:var(--mu)}"
 ".wx-attr{font-size:.74rem;color:var(--mu);margin-top:10px}"
 ".wx-attr a{color:var(--mu)}"
 # voter registration card
 ".vote-card{background:#fff;border:1px solid #e3eae6;border-top:4px solid var(--gold);border-radius:10px;padding:20px}"
 ".vote-card h3{font-size:1rem;color:var(--gd);margin-bottom:10px}"
 ".vote-card ul{list-style:none}.vote-card li{padding:6px 0;border-bottom:1px dashed #e3eae6;font-size:.92rem}"
 ".vote-card li:last-child{border-bottom:none}.vote-card a{color:var(--blue);text-decoration:none;font-weight:600}"
 # region link (city pages) + did-you-know (county pages)
 "a.pill{text-decoration:none}a.pill:hover{background:rgba(255,255,255,.25)}.region-link{margin:6px 0 0;font-size:.92rem}.region-link a{color:var(--g);font-weight:700;text-decoration:none}"
 ".did-you-know{background:var(--bg);border-left:4px solid var(--gold);border-radius:6px;padding:12px 16px;margin:18px 0 0}.did-you-know a{color:var(--blue);font-weight:600}"
 # blog (index cards + article body)
 ".post-meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}.post{max-width:760px;font-size:1.04rem;margin-top:20px}.post p{margin:0 0 16px}"
 ".post h2{font-size:1.45rem;color:var(--gd);margin:38px 0 14px;border-bottom:3px solid var(--g);padding-bottom:8px}"
 ".post h3{font-size:1.15rem;color:var(--gd);margin:26px 0 10px}.post ul,.post ol{padding-left:22px;margin:0 0 16px}.post li{padding:3px 0}"
 ".post a{color:var(--blue)}.post .lede{font-size:1.14rem;color:var(--tx)}.post .tbl{font-size:.92rem}"
 ".callout{background:var(--bg);border:1px solid #e3eae6;border-left:5px solid var(--gold);border-radius:8px;padding:16px 18px;margin:22px 0}.callout p:last-child{margin:0}"
 ".town-facts{font-size:.88rem;color:var(--mu);margin:-4px 0 12px}"
 ".visit-card{background:var(--bg);border:1px solid #e3eae6;border-left:5px solid var(--g);border-radius:8px;padding:12px 16px;margin:-4px 0 18px;font-size:.93rem;display:flex;flex-wrap:wrap;gap:4px 18px}"
 ".visit-card strong{flex-basis:100%;color:var(--gd)}.visit-card span{white-space:normal}.visit-card a{color:var(--blue);font-weight:600;text-decoration:none}.visit-card a:hover{text-decoration:underline}"
 ".cta-box{background:linear-gradient(135deg,#0b2418 0%,#14382a 45%,#1f4e79 100%);color:#fff;border-radius:12px;padding:28px;margin:36px 0 10px}"
 ".cta-box h2{color:#fff;border:none;margin:0 0 10px;padding:0}.cta-box p{color:#dceee3}.cta-box .btn-cta{margin-top:6px}.cta-box .btn-ghost{margin:6px 0 0 8px}"
 ".post-card{display:flex;flex-direction:column;text-decoration:none;color:inherit}.post-card .pc-cat{text-transform:uppercase;letter-spacing:.12em;font-size:.72rem;font-weight:700;color:#9a7a2c}"
 ".post-card h3{font-size:1.15rem;margin:8px 0}.post-card p{font-size:.93rem;color:var(--tx);flex:1}.post-card .pc-date{font-size:.82rem;color:var(--mu);margin-top:12px}"
 ".post-card .pc-more{color:var(--blue);font-weight:700;font-size:.9rem;margin-top:6px}"
)

OREGON_TICKER_FACTS = [
 "Oregon has the only two-sided state flag in the US 🦫",
 "Crater Lake is the deepest lake in the US at 1,943 feet deep 🏔",
 "Oregon beaches are 100% publicly owned by law — no private beach access 🌊",
 "Oregon has no statewide sales tax 💰",
 "The world's largest living organism is in Oregon — a honey fungus spanning 2.4 miles in Malheur National Forest 🍄",
 "Portland has the world's smallest park: Mill Ends Park, just 2 feet in diameter 🌳",
 "Oregon grows 99% of the US hazelnut crop 🌰",
 "Portland's Powell's Books is one of the world's largest independent bookstores 📚",
 "Nike was founded in Oregon in 1964 by Phil Knight and Bill Bowerman 👟",
 "Multnomah Falls drops 620 feet — one of the tallest year-round waterfalls in the US 💧",
 "Oregon was the first state to vote entirely by mail 📬",
 "Oregon City (1844) was the first incorporated city west of the Rocky Mountains 🏙",
 "Oregon has 40+ covered bridges — more than any other western state 🌉",
 "The Oregon Dunes are the largest coastal sand dune system in North America 🏜",
 "Smith Rock State Park is considered the birthplace of American sport climbing 🧗",
 "Oregon's state nut is the hazelnut 🌰",
 "Oregon is the #1 US producer of Christmas trees 🎄",
 "Crater Lake gets an average of 533 inches of snow per year ❄",
 "Silver Falls State Park's Trail of Ten Falls passes 10 waterfalls in just 7.2 miles 🏞",
 "Oregon's Sea Lion Caves near Florence is the only mainland year-round wild sea lion habitat in the US 🦭",
 "The Columbia River Gorge has 77 named waterfalls 💦",
 "Oregon has 300+ craft breweries — among the most per capita in the US 🍺",
 "Astoria (1811) is the oldest American settlement west of the Rocky Mountains ⚓",
 "Mt. Hood is climbed by 10,000+ people every year 🏔",
 "The Willamette Valley produces world-class Pinot Noir wine 🍷",
 "Tillamook County Creamery makes 167,000 pounds of cheese per day 🧀",
 "Oregon's state bird is the Western Meadowlark 🐦",
 "Portland was named by a coin flip between settlers from Portland ME and Boston MA 🪙",
 "Oregon's Painted Hills have layers of red, tan and black from 35 million years of volcanic history 🎨",
 "The Pacific Crest Trail runs 430 miles through Oregon 🥾",
 "Oregon's state mushroom is the Pacific Golden Chanterelle 🍄",
 "The Wallowa Mountains in NE Oregon are nicknamed 'Oregon's Alps' 🏔",
 "Oregon's state tree is the Douglas Fir — the most common lumber tree in North America 🌲",
 "Mt. Hood is Oregon's highest peak at 11,249 feet 🗻",
 "The Oregon Trail carried 400,000+ settlers from Missouri to Oregon in the 1840s–60s 🐂",
 "Oregon's Crater Lake is so clear you can see 100+ feet into the water 🔵",
 "The Timberline Lodge on Mt. Hood was hand-built by craftsmen in 1937 as a WPA project 🏛",
 "Oregon's Columbia River Gorge is a National Scenic Area 80 miles long 🌄",
 "The Rogue River runs entirely within Oregon for 215 miles 🚣",
 "Oregon's state fish is the Chinook Salmon 🐟",
 "Portland's International Rose Test Garden has over 10,000 rose bushes 🌹",
 "Oregon's bottle bill (1971) was the first container deposit law in the US ♻",
 "Oregon's Astoria Column has a 164-step spiral staircase with panoramic views 🌀",
 "Crater Lake was formed 7,700 years ago when Mt. Mazama collapsed 🌋",
 "Oregon has 14 national forests covering millions of acres 🌲",
 "The Oregon Shakespeare Festival in Ashland runs February through October 🎭",
 "Oregon has more than 100 state parks 🏕",
 "Bonneville Dam (1938) on the Columbia River was one of the first great New Deal hydropower projects ⚡",
 "Oregon's Pendleton Round-Up (est. 1910) is one of the top 5 rodeos in the US 🤠",
 "Oregon's state flower is the Oregon Grape 🌿",
 "Portland's Hawthorne Bridge (1910) is the oldest operating vertical-lift bridge in the US 🌉",
 "Intel employs over 20,000 people in Hillsboro, Oregon 💻",
 "The John Day Fossil Beds contain 50+ million years of continuous fossils 🦴",
 "Oregon's Malheur National Wildlife Refuge hosts over 320 bird species 🦅",
 "Oregon's Harney County is bigger than Maryland and Delaware combined 🗺",
 "The Willamette Meteorite (1902) is the largest meteorite ever found in the US ☄",
 "Oregon's state motto: 'She Flies with Her Own Wings' 🦅",
 "Eugene's Prefontaine Memorial Trail honors Steve Prefontaine, who held 7 American track records 🏃",
 "Oregon's McKenzie River near Eugene is rated one of the top trout streams in the West 🎣",
 "Oregon Caves in Josephine County are still being formed by moving water today 🕳",
 "The Oregon Coast Aquarium in Newport has a massive open-ocean exhibit 🦈",
 "Oregon's state insect is the Oregon Swallowtail butterfly 🦋",
 "Portland's MAX light rail (opened 1986) is one of the longest light rail systems in the US 🚇",
 "Oregon's Forest Park in Portland is one of the largest urban forests in the US, at over 5,000 acres 🌳",
 "The Columbia River produces more hydropower than any other river in North America ⚡",
 "Oregon's Pacific Flyway is a major migratory route for birds from Alaska to Baja California 🦆",
 "Portland's Lan Su Chinese Garden is the largest authentic Suzhou-style garden outside China 🏯",
 "Oregon's state rock is the thunder egg — a type of geode found in volcanic ash beds ⚡🥚",
 "Oregon has more than 600 lakes over 10 acres in size 🏞",
 "Silver Falls is Oregon's largest state park at 9,000+ acres 🌲",
 "Oregon's Sea Lion Caves are accessible by elevator carved into the cliff ⬇",
 "The original Oregon Territory (1848) included modern Oregon, Washington, Idaho and parts of Montana 🗺",
 "Oregon's Willamette Valley is the #1 US producer of grass seed 🌾",
 "Oregonians consume more coffee per capita than almost any other US state ☕",
 "Portland has over 500 food carts — one of the most vibrant food cart cultures in the country 🌮",
 "Oregon's Crater Lake has a small island called Wizard Island formed by a cinder cone 🌋",
 "The Umpqua River is considered one of the oldest river systems in the Cascade Range 🏔",
 "Oregon's Newberry Volcanic National Monument contains one of North America's largest calderas 🌋",
 "Oregon's state fossil is Metasequoia (dawn redwood) 🌲",
 "The Alvord Desert in southeast Oregon is one of the driest places in the Pacific Northwest ☀",
 "Steens Mountain in SE Oregon rises 9,773 feet above the desert floor 🏔",
 "Portland's Saturday Market (est. 1974) is the largest continuously operating outdoor arts market in the US 🎨",
 "Oregon's Tillamook Air Museum houses one of the world's largest wooden structures 🛩",
 "The Pacific Ring of Fire runs through Oregon — several volcanoes are still considered active 🌋",
 "Oregon's Mt. Jefferson is the 2nd highest peak in the state at 10,495 feet 🗻",
 "Oregon has more designated Wild and Scenic Rivers than any other state 🚣",
 "Oregon is one of only 5 states with no general sales tax 💵",
 "The Astoria-Megler Bridge (1966) crossing the Columbia River is 4.1 miles long 🌉",
 "Oregon banned self-serve gas for 72 years — since 2023, drivers statewide may pump their own ⛽",
 "Oregon's Fort Clatsop near Astoria is where Lewis and Clark spent winter 1805–1806 ⛺",
 "Oregon's 1000 Friends (est. 1975) pioneered land-use planning to protect farmland from sprawl 🌾",
 "Oregon has 13 National Wildlife Refuges 🦅",
 "Portland's Union Station has been an active train station since 1896 🚂",
 "Oregon's Crater Lake National Park was established in 1902 — Oregon's only national park 🏞",
 "Oregon is one of the top US producers of peppermint oil 🌿",
 "The Fremont Bridge in Portland (1973) has the longest tied-arch span in the US at 1,255 feet 🌉",
 "Oregon's 'Open Beaches Act' (1967) ensures all Oregon beaches are publicly accessible 🏖",
 "Oregon's Lan Su Chinese Garden in Portland was built by 65 craftspeople from Suzhou, China 🪷",
 "Oregon became the 33rd state on February 14, 1859 — Valentine's Day 💘",
 "The beaver is Oregon's state animal, which is why it's called the Beaver State 🦫",
 "Haystack Rock at Cannon Beach rises 235 feet from the sand 🪨",
 "Hells Canyon on the Oregon–Idaho border is North America's deepest river gorge 🏞",
]


def ticker_html():
    """Infinite horizontal fact ticker — CSS animation only; facts duplicated so translateX(-50%) loops seamlessly."""
    spans = ''.join(f'<span>{e(f)}</span>' for f in OREGON_TICKER_FACTS)
    return f'<div class="ticker" role="region" aria-label="Oregon fun facts"><div class="ticker-track">{spans}{spans}</div></div>'


ALERTS_JS = ("<script>(function(){var d=document.getElementById('alerts-bar'),done=false;if(!d)return;"
 "d.addEventListener('toggle',function(){if(!d.open||done)return;done=true;var box=document.getElementById('ab-live');"
 "var src='https://traveloregon.com/wp-json/wp/v2/pages?slug=travel-alerts&_fields=content';"
 "var ctl=window.AbortController?new AbortController():null;if(ctl)setTimeout(function(){ctl.abort()},9000);"
 "fetch('https://api.allorigins.win/get?url='+encodeURIComponent(src),ctl?{signal:ctl.signal}:{}).then(function(r){return r.json()})"
 ".then(function(j){var a=JSON.parse(j.contents);var h=a&&a[0]&&a[0].content&&a[0].content.rendered;if(!h)return;"
 "var doc=new DOMParser().parseFromString(h,'text/html'),items=[];"
 "doc.querySelectorAll('h2,h3,h4,p,li').forEach(function(n){var t=(n.textContent||'').replace(/\\s+/g,' ').trim();if(t.length>25&&items.length<6)items.push(t)});"
 "if(!items.length)return;var hd=document.createElement('h4');hd.textContent='Latest from Travel Oregon';box.appendChild(hd);"
 "items.forEach(function(t){var p=document.createElement('p');p.textContent=t.length>300?t.slice(0,297)+'\\u2026':t;box.appendChild(p)});"
 "var s=document.createElement('p');s.className='ab-note';s.textContent='Live excerpt \\u2014 see the full alerts page for details.';box.appendChild(s);"
 "}).catch(function(){});});})();</script>")


def alert_banner():
    """Collapsed travel-alert bar on every page; live Travel Oregon text is fetched on first expand (silent fail)."""
    ext = 'target="_blank" rel="noopener"'
    return ('<details id="alerts-bar"><summary>&#9888;&#65039; Oregon Travel Alerts &mdash; Road Closures &amp; Wildfire Safety</summary><div class="ab"><div class="ab-grid">'
            f'<div><strong class="abh">&#128679; Road Conditions</strong><ul><li><a href="https://www.tripcheck.com/" {ext}>TripCheck.com</a> &mdash; ODOT closures, cameras &amp; chain rules</li><li>Dial <strong>511</strong> for road info by phone</li></ul></div>'
            f'<div><strong class="abh">&#128293; Wildfire Safety</strong><ul><li><a href="https://wildfire.oregon.gov/" {ext}>Oregon Wildfire Response &amp; Recovery</a></li><li><a href="https://fire.airnow.gov/" {ext}>AirNow Fire &amp; Smoke Map</a></li></ul></div>'
            f'<div><strong class="abh">&#128226; Alerts &amp; Updates</strong><ul><li><a href="https://traveloregon.com/travel-alerts/" {ext}>Travel Oregon travel alerts</a></li><li><a href="https://www.oralert.gov/" {ext}>ORAlert.gov</a> &mdash; sign up for emergency alerts</li></ul></div>'
            '</div><div id="ab-live" aria-live="polite"></div></div></details>' + ALERTS_JS)


OR_BBOX = (41.92, 46.34, -124.62, -116.38)   # lat_min, lat_max, lon_min, lon_max
OR_OUTLINE = [  # (lon, lat), clockwise from the Columbia River mouth
    (-124.03, 46.26), (-123.55, 46.26), (-123.2, 46.17), (-122.9, 46.1), (-122.8, 45.86), (-122.77, 45.65),
    (-122.4, 45.58), (-121.9, 45.66), (-121.5, 45.72), (-121.2, 45.61), (-120.9, 45.65), (-120.5, 45.7),
    (-120.0, 45.82), (-119.6, 45.92), (-119.25, 45.93), (-118.98, 46.0), (-116.92, 46.0), (-116.78, 45.85),
    (-116.55, 45.5), (-116.46, 45.2), (-116.7, 45.0), (-116.85, 44.75), (-117.15, 44.48), (-117.22, 44.3),
    (-116.97, 44.2), (-116.9, 43.95), (-117.03, 43.8), (-117.03, 42.0), (-120.0, 42.0), (-122.5, 42.0),
    (-124.21, 42.0), (-124.36, 42.25), (-124.42, 42.66), (-124.52, 42.87), (-124.39, 43.3), (-124.25, 43.45),
    (-124.12, 43.75), (-124.1, 44.2), (-124.06, 44.6), (-124.02, 45.0), (-123.97, 45.5), (-123.93, 45.9),
    (-123.98, 46.2), (-124.03, 46.26)]


def _or_xy(lat, lon, w=200, h=160, pad=8):
    la0, la1, lo0, lo1 = OR_BBOX
    return (lon - lo0) / (lo1 - lo0) * (w - 2 * pad) + pad, (la1 - lat) / (la1 - la0) * (h - 2 * pad) + pad


def oregon_svg_map(lat, lon, label='City'):
    pts = ' '.join('%.1f,%.1f' % _or_xy(la, lo) for lo, la in OR_OUTLINE)
    x, y = _or_xy(lat, lon)
    return (f'<figure class="ormap"><svg viewBox="0 0 200 160" width="200" height="160" role="img" aria-label="Map of Oregon showing the location of {e(label)}">'
            f'<polygon points="{pts}" fill="#dfeee5" stroke="#1a5632" stroke-width="1.5" stroke-linejoin="round"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#d62828" stroke="#fff" stroke-width="1.5"><title>{e(label)}</title></circle>'
            f'</svg><figcaption>Location in Oregon</figcaption></figure>')


def oregon_silhouette(w=500, h=400, cls='or-sil'):
    """Large decorative Oregon outline (inline SVG) for hero backgrounds."""
    pts = ' '.join('%.1f,%.1f' % _or_xy(la, lo, w, h, 10) for lo, la in OR_OUTLINE)
    return (f'<svg class="{cls}" viewBox="0 0 {w} {h}" aria-hidden="true" focusable="false">'
            f'<polygon points="{pts}" fill="rgba(255,255,255,.07)" stroke="rgba(255,255,255,.6)" stroke-width="2.5" stroke-linejoin="round"/></svg>')


def city_tagline(name, county, region):
    t = CITY_TAGLINES.get(slug(name))
    if t: return t
    return f'{name} \u2014 {county} County \u00b7 ' + (region if region.endswith('Oregon') else f'{region}, Oregon')


def hero_style(rname):
    a, b, _ = REGION_THEME.get(rname, ('#14382a', '#1a5632', ''))
    return f' style="background:linear-gradient(135deg,{a} 0%,{b} 100%)"'


def slug(name):
    if name in SLUG_OVERRIDES: return SLUG_OVERRIDES[name]
    s = name.lower().replace('.', '').replace("'", '').replace(' ', '-')
    while '--' in s: s = s.replace('--', '-')
    return s.strip('-')


def e(t):
    return html.escape(str(t), quote=True)


def n(v):
    try: return f'{int(float(v)):,}'
    except (TypeError, ValueError): return ''


def host(url):
    return re.sub(r'^https?://(www\.)?', '', url).rstrip('/')


def miles(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a['lat'], a['lon'], b['lat'], b['lon']))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def summary_html(text, limit=1100):
    """Clean a Wikipedia intro (drop stripped pronunciation guides) and trim to whole paragraphs/sentences."""
    text = re.sub(r' \(\s[^)]*\)', '', text or '')
    text = re.sub(r'\s+([,.])', r'\1', text)
    out, total = [], 0
    for para in [p.strip() for p in text.split('\n') if p.strip()]:
        if total + len(para) > limit and out: break
        if len(para) > limit:
            cut = para[:limit]
            para = cut[:cut.rfind('. ') + 1] if '. ' in cut else cut
        out.append(para); total += len(para)
    return ''.join(f'<p>{e(p)}</p>' for p in out)


def head(title, desc, path, og_type='website', image=None, extra='', up='', keywords=''):
    url = f'{BASE_URL}{path}'
    img = image or DEFAULT_IMG
    ga = (f'<script async src="https://www.googletagmanager.com/gtag/js?id={ANALYTICS_ID}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","{ANALYTICS_ID}");</script>' if ANALYTICS_ID else '')
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{e(title)}</title>'
            f'<meta name="description" content="{e(desc)}">' + (f'<meta name="keywords" content="{e(keywords)}">' if keywords else '') + '<meta name="robots" content="index, follow">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            f'<link rel="icon" href="{up}assets/favicon.ico"><link rel="apple-touch-icon" href="{up}assets/favicon-32.png"><link rel="canonical" href="{url}">'
            f'<meta property="og:site_name" content="{SITE_NAME}"><meta property="og:type" content="{og_type}">'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
            f'<meta property="og:url" content="{url}"><meta property="og:image" content="{e(img)}">'
            f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}">'
            f'<meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{e(img)}">'
            f'{extra}{ga}<style>{CSS}</style></head><body>')


def header(up):
    return (f'<header class="hd"><div class="wrap"><nav><a class="logo" href="{up}index.html"><span class="badge">&#127795;</span> Oregon Information</a>'
            f'<ul class="nl"><li><a href="{up}moving-to-oregon/index.html">Moving</a></li><li><a href="{up}visit-oregon/index.html">Visiting</a></li>'
            f'<li><a href="{up}regions/index.html">Regions</a></li>'
            f'<li><a href="{up}counties/index.html">Counties</a></li><li><a href="{up}cities/index.html">Cities A&ndash;Z</a></li><li><a href="{up}blog/index.html">Blog</a></li></ul></nav></div></header>')


def footer(up, note=''):
    return (f'<footer class="ft"><div class="wrap"><p class="fl"><a href="{up}about/index.html">About</a><a href="{up}contact/index.html">Contact</a>'
            f'<a href="{up}privacy/index.html">Privacy Policy</a><a href="{up}regions/index.html">Regions</a>'
            f'<a href="{up}cities/index.html">Cities</a><a href="{up}counties/index.html">Counties</a><a href="{up}blog/index.html">Blog</a></p>'
            f'<p>&copy; 2026 Oregon Information &mdash; independent resource, not affiliated with the State of Oregon.{note}</p></div></footer></body></html>')


def ld(obj):
    return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>'


def file_page(item):
    f = item.get('image_file', '')
    if not f: return ''
    base = 'https://en.wikipedia.org' if '/wikipedia/en/' in (item.get('image') or '') else 'https://commons.wikimedia.org'
    return f'{base}/wiki/File:{f}'


def photo(item, alt):
    if not item.get('image'): return ''
    f = item.get('image_file', '')
    credit = f'<a href="{e(file_page(item))}" target="_blank" rel="noopener">Wikimedia</a>' if f else 'Wikimedia Commons'
    fit = ' style="object-fit:contain"' if f.lower().endswith(('.svg', '.png')) else ''
    return (f'<figure class="photo"><img src="{e(item["image"])}"{fit} alt="{e(alt)}" loading="lazy">'
            f'<figcaption>Image: {credit} (see file page for author and license)</figcaption></figure>')


CITY_IMAGES = json.load(open('data/city_images.json', encoding='utf-8')) if os.path.exists('data/city_images.json') else {}
LINK_FIXES = json.load(open('data/link_fixes.json', encoding='utf-8')) if os.path.exists('data/link_fixes.json') else {}
DEAD_LINKS = set(json.load(open('data/dead_links.json', encoding='utf-8'))) if os.path.exists('data/dead_links.json') else set()


def fix_url(u):
    return LINK_FIXES.get(u, u) if u else u


GALLERY_EXCLUDE = json.load(open('data/gallery_exclude.json', encoding='utf-8')) if os.path.exists('data/gallery_exclude.json') else {}
CITY_SCHOOLS = json.load(open('data/city_schools.json', encoding='utf-8')) if os.path.exists('data/city_schools.json') else {}


JUNK_WORDS = ('cemetery', 'greyhound', 'crucible', 'corbett hill', 'national forest historic photo', 'grave', '500px provided', 'photo by', 'odfw')


def clean_cap(s, name):
    s = re.sub(r'<[^>]+>', '', s or '').split('\n')[0]
    s = re.sub(r'\b(w|en|wikipedia):', '', s)
    s = re.sub(r'\s+', ' ', s).strip(' .-')
    return s if 3 <= len(s) else f'{name}, Oregon'


def norm_file(f):
    """Normalize a Commons filename so 'A_b%2C.jpg' and 'A b,.jpg' compare equal."""
    from urllib.parse import unquote
    f = unquote(f or '').split('/')[-1]
    f = re.sub(r'^(file|image):', '', f, flags=re.I)
    return re.sub(r'[\s_]+', ' ', f).strip().lower()


def gallery(c, name):
    imgs = [i for i in CITY_IMAGES.get(name, []) if i.get('src')
            and not any(w in (i.get('file', '') + ' ' + (i.get('caption') or '')).lower() for w in JUNK_WORDS)]
    main_file = norm_file(c.get('image_file'))
    main_ok = c.get('image') and not any(w in main_file for w in ('map', 'locator', 'area', '.svg', '.png', 'seal', 'flag', 'logo'))
    figs = []
    seen = {norm_file(x) for x in GALLERY_EXCLUDE.get(name, [])}  # hand-picked near-duplicates
    if main_ok:
        seen.add(main_file)
        m = next((i for i in imgs if norm_file(i.get('file')) == main_file), None)
        if m:  # same photo is in the gallery data: reuse its real caption and credit
            figs.append((c['image'], clean_cap(m.get('caption'), name), m.get('page') or file_page(c), m.get('artist') or 'Wikimedia Commons', m.get('license') or ''))
        else:
            figs.append((c['image'], f'{name}, Oregon', file_page(c), 'Wikipedia' if '/wikipedia/en/' in c['image'] else 'Wikimedia Commons', ''))
    for i in imgs:
        key = norm_file(i.get('file')) or i['src']
        if key in seen: continue
        seen.add(key)
        figs.append((i['src'], clean_cap(i.get('caption'), name), i.get('page') or '', i.get('artist') or 'Wikimedia Commons', i.get('license') or ''))
    figs = figs[:6]
    if not figs:
        return photo(c, f'{name}, Oregon')
    out = []
    for src, cap, page, artist, lic in figs:
        credit = f'{e(artist)}' + (f', {e(lic)}' if lic else '')
        link = f' &middot; <a href="{e(page)}" target="_blank" rel="noopener">source</a>' if page else ''
        out.append(f'<figure><img src="{e(src)}" alt="{e(cap)}" loading="lazy"><figcaption>{e(cap if len(cap) <= 90 else cap[:88].rsplit(" ", 1)[0].rstrip(",;:") + "…")}<br><small>Photo: {credit}{link}</small></figcaption></figure>')
    return f'<h2 class="st">{e(name)} in Pictures</h2><section class="gallery g{min(len(figs),3)}">{"".join(out)}</section>'


def wiki_credit(item):
    return (f'<p class="src">Source: adapted from <a href="{e(item["wiki_url"])}" target="_blank" rel="noopener">Wikipedia</a>, '
            f'available under <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a>.</p>')


def faq_for(city, county, region, electric):
    k = sum(ord(c) for c in city) % 3
    q = [
     (f"What is the cost of living in {city}, Oregon?", f"{city} lies in the {region} region, where costs vary mainly by housing. Oregon charges no statewide sales tax."),
     (f"What utilities do I set up when moving to {city}?", f"Electricity in this area is generally provided by {electric} (confirm by address); natural gas, where available, by NW Natural, Avista or Cascade Natural Gas. Water, sewer, and trash are typically arranged through the City of {city}."),
     (f"How do I find a job near {city}?", "WorkSource Oregon offers free career coaching, and iMatchSkills is the state's largest job board."),
     (f"Which schools serve families in {city}?", f"Assignment depends on your exact address. Start with the Oregon Department of Education directory or the {county} County district office."),
     (f"How soon must I register my car after moving to {city}?", "Within 30 days of establishing residency — both the vehicle registration and an Oregon driver's license."),
     (f"Are there food banks or assistance programs near {city}?", f"Yes. Apply for SNAP at the ONE Oregon portal, find a pantry through Oregon Food Bank, or dial 211 for {county} County community resources."),
    ]
    if k == 1: q[0] = (f"Is {city}, Oregon affordable to live in?", q[0][1]); q[2] = (f"What is the job market like around {city}?", q[2][1])
    elif k == 2: q[1] = (f"How do I connect utilities in {city}?", q[1][1]); q[4] = (f"After moving to {city}, what's the DMV deadline?", q[4][1])
    return q


def county_links(counties_str, up):
    return ', '.join(f'<a href="{up}counties/{slug(c)}/index.html">{e(c)} County</a>' for c in counties_str)


def voter_card(county, city_name):
    """Voter registration card with county election office link and Oregon SOS online registration."""
    clerk_url = COUNTY_ELECTIONS.get(county, 'https://sos.oregon.gov/voting/pages/registration.aspx')
    ext = ' target="_blank" rel="noopener"'
    items = [
        f'<li><strong>Oregon is a vote-by-mail state</strong> &mdash; ballots are mailed automatically to all registered voters</li>',
        f'<li><a href="https://secure.sos.state.or.us/orestar/guestLogin.do"{ext}>&#9989; Register or update your registration online (Oregon SOS)</a></li>',
        f'<li><a href="{e(clerk_url)}"{ext}>&#127970; {e(county)} County Elections Office</a> &mdash; local voter info, drop boxes &amp; ballot status</li>',
        f'<li><a href="https://sos.oregon.gov/voting/pages/registration.aspx"{ext}>Oregon Secretary of State &mdash; Voting &amp; Elections</a></li>',
        f'<li><a href="https://www.vote411.org/"{ext}>Vote411 &mdash; nonpartisan voter guide for {e(city_name)} area candidates</a></li>',
    ]
    return f'<div class="vote-card"><h3>&#127963; Register to Vote in {e(city_name)}</h3><ul>{"".join(items)}</ul></div>'


WMO_ICONS = {
    0:'☀️|Clear sky', 1:'🌤|Mainly clear', 2:'⛅|Partly cloudy', 3:'☁️|Overcast',
    45:'🌫|Fog', 48:'🌫|Icy fog',
    51:'🌦|Light drizzle', 53:'🌦|Drizzle', 55:'🌧|Heavy drizzle',
    61:'🌧|Light rain', 63:'🌧|Rain', 65:'🌧|Heavy rain',
    71:'🌨|Light snow', 73:'🌨|Snow', 75:'❄️|Heavy snow', 77:'🌨|Snow grains',
    80:'🌦|Rain showers', 81:'🌧|Heavy showers', 82:'⛈|Violent showers',
    85:'🌨|Snow showers', 86:'❄️|Heavy snow showers',
    95:'⛈|Thunderstorm', 96:'⛈|T-storm + hail', 99:'⛈|Heavy T-storm + hail',
}

def weather_widget(city_name, lat, lon):
    """Live weather card powered by Open-Meteo (free, no API key required)."""
    if lat is None or lon is None:
        return ''
    city_id = re.sub(r'[^a-z0-9]', '', city_name.lower())
    icons_js = '{' + ','.join(f'{k}:["{v.split("|")[0]}","{v.split("|")[1]}"]' for k, v in WMO_ICONS.items()) + '}'
    js = f"""<script>(function(){{
var lat={lat:.5f},lon={lon:.5f},WI={icons_js};
var days=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
fetch('https://api.open-meteo.com/v1/forecast?latitude='+lat+'&longitude='+lon
 +'&current=temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m'
 +'&daily=temperature_2m_max,temperature_2m_min,weather_code'
 +'&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=America%2FLos_Angeles&forecast_days=7')
.then(function(r){{return r.json();}})
.then(function(d){{
 var c=d.current,dl=d.daily,wi=WI[c.weather_code]||['🌡','Unknown'];
 var h='<div class="wx-cur"><span class="wx-icon">'+wi[0]+'</span>'
  +'<span class="wx-temp">'+Math.round(c.temperature_2m)+'&deg;F</span>'
  +'<span class="wx-cond">'+wi[1]+'</span>'
  +'<span class="wx-wind">&#128168; '+Math.round(c.wind_speed_10m)+' mph</span>'
  +'<span class="wx-humid">&#128167; '+Math.round(c.relative_humidity_2m)+'% humidity</span></div>';
 h+='<div class="wx-forecast">';
 for(var i=1;i<Math.min(7,dl.time.length);i++){{
  var dt=new Date(dl.time[i]+'T12:00:00'),fi=WI[dl.weather_code[i]]||['🌡',''];
  h+='<div class="wx-day"><div class="wx-day-name">'+days[dt.getDay()]+'</div>'
   +'<div class="wx-day-icon">'+fi[0]+'</div>'
   +'<div class="wx-day-hi">'+Math.round(dl.temperature_2m_max[i])+'&deg;</div>'
   +'<div class="wx-day-lo">'+Math.round(dl.temperature_2m_min[i])+'&deg;</div></div>';
 }}
 h+='</div><p class="wx-attr">Source: <a href="https://open-meteo.com/" target="_blank" rel="noopener">Open-Meteo</a> (real-time, NWS/NOAA data). Updated on page load.</p>';
 var el=document.getElementById('wx-{city_id}');if(el)el.innerHTML=h;
}})
.catch(function(){{
 var el=document.getElementById('wx-{city_id}');
 if(el)el.innerHTML='<p class="wx-loading">Weather data unavailable &mdash; visit <a href="https://forecast.weather.gov/" target="_blank" rel="noopener">weather.gov</a> for current conditions.</p>';
}});
}})();</script>"""
    return (f'<div class="wx-card"><h3>&#127782; Current Weather in {e(city_name)}, Oregon</h3>'
            f'<div id="wx-{city_id}" class="wx-loading">Loading weather&hellip;</div></div>'
            + js)


def city_page(c, all_cities, custom):
    name = c['name']; counties = c['counties']; county = counties[0]
    region, electric = COUNTY_INFO.get(county, ('Oregon', 'Local utility'))
    x = custom.get(name.lower().replace(' ', '_'), {})
    employers = x.get('major_employers') or f'Employers in and around {name} and {county} County'
    if isinstance(employers, list): employers = ', '.join(employers)
    or_map = oregon_svg_map(c['lat'], c['lon'], f'{name}, Oregon') if c.get('lat') is not None else ''
    ext = ' target="_blank" rel="noopener"'
    district, district_url = x.get('school_district'), fix_url(x.get('school_district_url'))
    ccd = CITY_SCHOOLS.get(name, [])
    schools = []
    for s in (x.get('schools') or []):
        if not s.get('name'): continue
        url = fix_url(s.get('url'))
        if url in DEAD_LINKS:
            key = re.sub(r'[^a-z]', '', s['name'].lower().replace('high school', 'hs'))
            m = next((r for r in ccd if re.sub(r'[^a-z]', '', r['name'].lower().replace('high school', 'hs')) == key), None)
            url = m['url'] if m else None
        schools.append({'name': s['name'], 'url': url})
    if not schools and ccd:
        schools = [{'name': s['name'] + (f" ({s['level']}, grades {s['grades']})" if s.get('grades') else (f" ({s['level']})" if s.get('level') else '')), 'url': s['url']} for s in ccd]
        if not district:
            ds = sorted({s['district'] for s in ccd if s.get('district') and not s.get('charter')})
            district = ', '.join(ds[:2]) if ds else None
    if schools or district:
        items = []
        if district:
            dn = f'<a href="{e(district_url)}"{ext}>{e(district)}</a>' if district_url else e(district)
            items.append(f'<li><strong>District:</strong> {dn}</li>')
        for s in schools[:8]:
            items.append(f'<li><a href="{e(s["url"])}"{ext}>{e(s["name"])}</a></li>' if s.get('url') else f'<li>{e(s["name"])}</li>')
        if len(schools) > 8:
            more = district_url or 'https://www.oregon.gov/ode/pages/default.aspx'
            items.append(f'<li><a href="{e(more)}"{ext}>See all schools &rarr;</a></li>')
        schools_card = f'<div class="card"><h3>&#127891; Schools</h3><ul>{"".join(items)}</ul></div>'
    else:
        schools_card = f'<div class="card"><h3>&#127891; Schools</h3><ul><li>No public schools are located inside {e(name)} city limits &mdash; students attend schools in the surrounding {e(county)} County district</li><li><a href="https://nces.ed.gov/ccd/schoolsearch/"{ext}>Find the schools serving an address (NCES)</a></li><li><a href="https://www.oregon.gov/ode/pages/default.aspx"{ext}>Oregon Dept. of Education</a></li></ul></div>'
    attr = [a for a in (x.get('top_attractions') or []) if a.get('name')][:5]
    attractions_card = ''
    if attr:
        ai = ''.join((f'<li><a href="{e(a["url"])}"{ext}>{e(a["name"])}</a>' if a.get('url') else f'<li><strong>{e(a["name"])}</strong>')
                     + (f'<br><small>{e(a["desc"])}</small>' if a.get('desc') else '') + '</li>' for a in attr)
        attractions_card = f'<div class="card"><h3>&#127956; Top Attractions</h3><ul>{ai}</ul></div>'
    pop = n(c['pop2020'])
    area = c.get('area_sqmi')
    density = f'{float(c["pop2020"]) / float(area):,.0f} people per sq mi' if area and float(area) > 0 else ''
    status = 'Incorporated city'
    if c['capital']: status += ' &mdash; Oregon state capital and county seat'
    elif c['seat']: status += f' &mdash; county seat of {e(county)} County'
    rows = [('County' if len(counties) == 1 else 'Counties', county_links(counties, '../../')), ('Region', e(region)),
            ('Population (2020 Census)', pop or 'n/a'), ('Population (2010 Census)', n(c['pop2010']) or 'n/a'),
            ('Change 2010&ndash;2020', e(c['change']) or 'n/a')]
    if area: rows.append(('Land area', f'{float(area):g} sq mi'))
    if density: rows.append(('Population density', density))
    if c.get('incorporated'): rows.append(('Incorporated', e(c['incorporated'])))
    rows.append(('Status', status))
    if c.get('website'): rows.append(('Official city website', f'<a href="{e(c["website"])}" target="_blank" rel="noopener">{e(host(c["website"]))}</a>'))
    if c.get('lat') is not None: rows.append(('Coordinates', f'{c["lat"]:.4f}&deg; N, {abs(c["lon"]):.4f}&deg; W'))
    for k, label in (('nearest_hospital', 'Nearest major hospital'), ('transit', 'Public transit')):
        if x.get(k): rows.append((label, e(x[k])))
    facts = ''.join(f'<tr><th>{a}</th><td>{b}</td></tr>' for a, b in rows)
    near = sorted((miles(c, o), o) for o in all_cities if o is not c and o.get('lat') is not None and c.get('lat') is not None)[:6]
    near_html = ''.join(f'<a href="../{slug(o["name"])}/index.html">{e(o["name"])}<small>{d:.0f} mi &middot; pop. {n(o["pop2020"])}</small></a>' for d, o in near)
    fq = faq_for(name, county, region, electric)
    if pop: fq.insert(0, (f"What is the population of {name}, Oregon?", f"{name} had {pop} residents at the 2020 U.S. Census (up from {n(c['pop2010'])} in 2010)." if c['change'].startswith('+') else f"{name} had {pop} residents at the 2020 U.S. Census ({n(c['pop2010'])} in 2010)."))
    faq_details = '\n'.join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in fq)
    path = f'/cities/{slug(name)}/'
    breg = big_region(c)
    reg_phrase = breg if breg.endswith('Oregon') else f'{breg} Oregon'
    desc = (f'{name}, Oregon: a {county} County city' + (f' of {pop} people' if pop else '')
            + f'. Schools, utilities, weather, parks and moving resources for {name}, OR.')
    keywords = (f'{name}, {name} Oregon, {name} OR, {county} County Oregon, {reg_phrase}, moving to {name}, '
                f'{name} schools, {name} utilities, Oregon cities')
    tagline = city_tagline(name, county, breg)
    badges = ''.join(f'<span class="pill">{b}</span>' for b in (
        [f'&#128101; Pop. {pop}'] if pop else []) + [f'&#127963; {e(county)} County']
        + (['&#11088; State capital'] if c['capital'] else ['&#127963; County seat'] if c['seat'] else []))
    rslug = REGION_SLUGS.get(breg)
    badges += (f'<a href="../../regions/{rslug}/index.html" class="pill">&#128205; {e(breg)} Region</a>' if rslug
               else f'<span class="pill">&#128205; {e(breg)}</span>')
    city_ld = {'@context': 'https://schema.org', '@type': 'City', 'name': f'{name}, Oregon', 'url': f'{BASE_URL}{path}',
               'containedInPlace': {'@type': 'AdministrativeArea', 'name': f'{county} County, Oregon'}}
    if c.get('lat') is not None: city_ld['geo'] = {'@type': 'GeoCoordinates', 'latitude': c['lat'], 'longitude': c['lon']}
    same = [u for u in (c.get('wiki_url'), c.get('website')) if u]
    if same: city_ld['sameAs'] = same
    if c.get('image'): city_ld['image'] = c['image']
    bread = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{BASE_URL}/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Oregon Cities', 'item': f'{BASE_URL}/cities/'},
        {'@type': 'ListItem', 'position': 3, 'name': f'{county} County', 'item': f'{BASE_URL}/counties/{slug(county)}/'},
        {'@type': 'ListItem', 'position': 4, 'name': name, 'item': f'{BASE_URL}{path}'}]}
    faq_ld = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in fq[:5]]}
    sl = '\n'.join(f'<li><a href="{u}" target="_blank" rel="noopener">{t}</a></li>' for t, u in STATE_LINKS)
    local = []
    if c.get('website'): local.append(f'<li><a href="{e(c["website"])}" target="_blank" rel="noopener">City of {e(name)} official website</a></li>')
    for cn in counties:
        cw = COUNTY_SITES.get(cn)
        if cw: local.append(f'<li><a href="{e(cw)}" target="_blank" rel="noopener">{e(cn)} County official website</a></li>')
    local.append(f'<li><a href="../../counties/{slug(county)}/index.html">{e(county)} County guide on Oregon Information</a></li>')
    if c.get('wiki_url'): local.append(f'<li><a href="{e(c["wiki_url"])}" target="_blank" rel="noopener">{e(name)} on Wikipedia</a></li>')
    lead = f'{e(name)} is an incorporated city in {county_links(counties, "../../")}, in Oregon&rsquo;s {e(region)} region' + (f', with a 2020 Census population of {pop}.' if pop else '.')
    wx = weather_widget(name, c.get('lat'), c.get('lon'))
    vote = voter_card(county, name)
    return (head(f'{name}, Oregon: Population, Schools, Weather & Moving Guide', desc, path, 'article', c.get('image'), ld(city_ld) + ld(bread) + ld(faq_ld), '../../', keywords)
            + header('../../') + ticker_html() + alert_banner()
            + f'<div class="hero city-hero"{hero_style(breg)}><div class="wrap"><h1>{e(name)}, Oregon</h1><p class="city-tagline">{e(tagline)}</p>'
            + f'<div class="pills">{badges}</div>'
            + f'<p class="hero-sub">{e(name)}, OR guide: population, schools, utilities, weather, attractions, nearby cities and a moving checklist for {e(county)} County, {e(reg_phrase)}.</p></div></div>'
            + f'<main><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><a href="../../index.html">Home</a> &rsaquo; <a href="../index.html">Oregon Cities</a> &rsaquo; <a href="../../counties/{slug(county)}/index.html">{e(county)} County</a> &rsaquo; {e(name)}</nav>'
            + (f'<p class="region-link"><a href="../../regions/{rslug}/index.html">Explore the {e(breg)} region &rarr;</a></p>' if rslug else '')
            + f'<h2 class="st">Quick Facts</h2><div class="qf"><section class="facts"><table>{facts}</table></section>{or_map}</div>'
            + wx
            + f'<h2 class="st">About {e(name)}</h2><section class="prose"><p>{lead}</p>{summary_html(c["summary"])}{wiki_credit(c) if c.get("wiki_url") else ""}</section>'
            + gallery(c, name)
            + f'<h2 class="st">Moving to {e(name)}</h2><div class="cards"><div class="card"><h3>&#9889; Utilities Checklist</h3><ul><li><strong>Electricity:</strong> {utility_links_html(electric)} (confirm by address)</li><li><strong>Natural gas:</strong> NW Natural, Avista or Cascade Natural Gas (where available)</li><li><strong>Water &amp; sewer:</strong> City of {e(name)}</li><li><strong>Trash:</strong> Franchised hauler &mdash; verify by service address</li><li><strong>Internet:</strong> Compare providers at the <a href="https://broadbandmap.fcc.gov/" target="_blank" rel="noopener">FCC broadband map</a></li></ul></div>'
            + f'<div class="card"><h3>&#128188; Jobs &amp; Economy</h3><ul><li><strong>Notable employers:</strong> {e(employers)}</li><li><a href="https://www.worksourceoregon.org/" target="_blank" rel="noopener">WorkSource Oregon (free)</a></li><li><a href="https://www.imatchskills.org/" target="_blank" rel="noopener">iMatchSkills job board</a></li></ul></div>'
            + '<div class="card"><h3>&#127968; Housing</h3><ul><li><a href="https://www.zillow.com/or/" target="_blank" rel="noopener">Zillow Oregon</a></li><li><a href="https://www.apartments.com/oregon/" target="_blank" rel="noopener">Apartments.com</a></li><li><a href="https://www.oregon.gov/ohcs/" target="_blank" rel="noopener">OHCS buyer/renter programs</a></li></ul></div>'
            + '<div class="card"><h3>&#128663; DMV Steps</h3><ul><li>Vehicle registration &amp; Oregon license within <strong>30 days</strong></li><li><a href="https://www.oregon.gov/odot/dmv/" target="_blank" rel="noopener">New resident guide</a></li><li><a href="https://www.oregon.gov/odot/dmv/pages/offices/index.aspx" target="_blank" rel="noopener">Find a DMV office</a></li></ul></div>'
            + schools_card + attractions_card
            + vote
            + '<div class="card"><h3>&#127973; Healthcare &amp; Assistance</h3><ul><li><a href="https://one.oregon.gov/" target="_blank" rel="noopener">ONE portal (OHP/SNAP)</a></li><li><a href="https://www.oregonfoodbank.org/" target="_blank" rel="noopener">Oregon Food Bank</a></li><li><a href="https://www.211info.org/" target="_blank" rel="noopener">Dial 211 for local help</a></li></ul></div></div>'
            + (f'<h2 class="st">Nearby Cities</h2><nav class="dir-list">{near_html}</nav>' if near_html else '')
            + f'<h2 class="st">Frequently Asked Questions</h2><section class="faq">{faq_details}</section>'
            + f'<h2 class="st">Local &amp; Official Links</h2><section class="faq"><ul>{"".join(local)}{sl}</ul></section>'
            + '<p class="back"><a href="../index.html">&larr; All Oregon Cities</a></p></div></main>'
            + footer('../../', '<br>Population: U.S. Census Bureau (2010, 2020). Background text: Wikipedia (CC BY-SA 4.0).'))


COUNTY_SITES = {}


def county_region_note(name, sub_region, members):
    """'Did you know?' line linking a county page to its 7-region page and its largest cities."""
    breg = BIG_REGION_MAP.get(sub_region, '')
    rslug = REGION_SLUGS.get(breg)
    if not rslug: return ''
    top = members[:3]
    cities = ''
    if top:
        links = [f'<a href="../../cities/{slug(c["name"])}/index.html">{e(c["name"])}</a>' for c in top]
        joined = links[0] if len(links) == 1 else ', '.join(links[:-1]) + ' and ' + links[-1]
        cities = f' Its largest {"city is" if len(top) == 1 else "cities are"} {joined}.'
    return (f'<p class="did-you-know"><strong>Did you know?</strong> {e(name)} County is part of the '
            f'<a href="../../regions/{rslug}/index.html">{e(breg)} region</a> of Oregon.{cities}</p>')


def county_page(k, cities):
    name = k['name']; region, electric = COUNTY_INFO.get(name, ('Oregon', 'Local utility'))
    members = sorted([c for c in cities if name in c['counties']], key=lambda c: -float(c['pop2020'] or 0))
    pop = n(k['pop2020']); area = k.get('area_sqmi')
    density = f'{float(k["pop2020"]) / float(area):,.1f} people per sq mi' if area and float(area) > 0 else ''
    seat = next((c for c in cities if c['name'] == k['seat']), None)
    seat_html = f'<a href="../../cities/{slug(seat["name"])}/index.html">{e(seat["name"])}</a>' if seat else e(k['seat'])
    rows = [('County seat', seat_html), ('Region', e(region)), ('Population (2020 Census)', pop), ('Land &amp; water area', f'{n(area)} sq mi' if area else 'n/a')]
    if density: rows.append(('Population density', density))
    rows += [('Established', e(k['est'])), ('Formed from', e(k['origin'])), ('Name origin', e(k['etymology'])),
             ('Incorporated cities', str(len(members))), ('Main electric utility', e(electric)), ('FIPS code', f'41{e(k["fips"])}')]
    if k.get('website'): rows.append(('Official county website', f'<a href="{e(k["website"])}" target="_blank" rel="noopener">{e(host(k["website"]))}</a>'))
    facts = ''.join(f'<tr><th>{a}</th><td>{b}</td></tr>' for a, b in rows)
    trs = ''.join(f'<tr><td><a href="../../cities/{slug(c["name"])}/index.html">{e(c["name"])}</a>{" &#9733;" if c["name"] == k["seat"] else ""}</td><td>{n(c["pop2020"])}</td><td>{e(c.get("incorporated", ""))}</td></tr>' for c in members)
    path = f'/counties/{slug(name)}/'
    desc = f'{name} County, Oregon: county seat {k["seat"]}, population {pop} (2020 Census), {len(members)} incorporated cities, history, and official links.'
    ld_obj = {'@context': 'https://schema.org', '@type': 'AdministrativeArea', 'name': f'{name} County, Oregon', 'url': f'{BASE_URL}{path}',
              'containedInPlace': {'@type': 'State', 'name': 'Oregon'}}
    if k.get('lat') is not None: ld_obj['geo'] = {'@type': 'GeoCoordinates', 'latitude': k['lat'], 'longitude': k['lon']}
    same = [u for u in (k.get('wiki_url'), k.get('website')) if u]
    if same: ld_obj['sameAs'] = same
    bread = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{BASE_URL}/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Oregon Counties', 'item': f'{BASE_URL}/counties/'},
        {'@type': 'ListItem', 'position': 3, 'name': f'{name} County', 'item': f'{BASE_URL}{path}'}]}
    links = []
    if k.get('website'): links.append(f'<li><a href="{e(k["website"])}" target="_blank" rel="noopener">{e(name)} County official website</a></li>')
    links += ['<li><a href="https://www.211info.org/" target="_blank" rel="noopener">211info &mdash; local assistance</a></li>',
              '<li><a href="https://www.oregon.gov/odot/dmv/pages/offices/index.aspx" target="_blank" rel="noopener">Find a DMV office</a></li>',
              '<li><a href="https://www.worksourceoregon.org/" target="_blank" rel="noopener">WorkSource Oregon</a></li>',
              '<li><a href="https://oregoncounties.org/" target="_blank" rel="noopener">Association of Oregon Counties</a></li>']
    if k.get('wiki_url'): links.append(f'<li><a href="{e(k["wiki_url"])}" target="_blank" rel="noopener">{e(name)} County on Wikipedia</a></li>')
    return (head(f'{name} County, Oregon: Cities, Population & Living Guide', desc, path, 'article', k.get('image'), ld(ld_obj) + ld(bread), '../../')
            + header('../../') + ticker_html() + alert_banner()
            + f'<div class="hero"><div class="wrap"><h1>{e(name)} County, Oregon</h1><p>County seat: {e(k["seat"])} &middot; {e(region)} region &middot; {len(members)} incorporated cities</p></div></div>'
            + f'<main><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><a href="../../index.html">Home</a> &rsaquo; <a href="../index.html">Oregon Counties</a> &rsaquo; {e(name)} County</nav>'
            + county_region_note(name, region, members)
            + f'<h2 class="st">Quick Facts</h2><section class="facts"><table>{facts}</table></section>'
            + f'<h2 class="st">About {e(name)} County</h2><section class="prose">{summary_html(k["summary"], 1400)}{wiki_credit(k) if k.get("wiki_url") else ""}</section>'
            + photo(k, f'{name} County, Oregon')
            + f'<h2 class="st">Cities in {e(name)} County</h2><table class="tbl"><tr><th>City</th><th>Population (2020)</th><th>Incorporated</th></tr>{trs}</table><p class="src">&#9733; county seat. Cities that span more than one county are listed in each.</p>'
            + f'<h2 class="st">Official &amp; Helpful Links</h2><section class="faq"><ul>{"".join(links)}</ul></section>'
            + '<p class="back"><a href="../index.html">&larr; All Oregon Counties</a></p></div></main>'
            + footer('../../', '<br>Population: U.S. Census Bureau 2020. Background text: Wikipedia (CC BY-SA 4.0).'))


def cities_index(cities):
    groups = {}
    for c in sorted(cities, key=lambda x: x['name'].lower()):
        groups.setdefault(c['name'][0].upper(), []).append(c)
    alpha = ''.join(f'<a href="#letter-{L.lower()}">{L}</a>' for L in groups)
    body = ''.join(f'<h3 class="letter" id="letter-{L.lower()}">{L}</h3><nav class="dir-list">' + ''.join(
        f'<a href="{slug(c["name"])}/index.html" data-n="{e(c["name"].lower())} {e(" ".join(c["counties"]).lower())}">{e(c["name"])}<small>{e(", ".join(c["counties"]))} Co. &middot; pop. {n(c["pop2020"])}</small></a>' for c in cs) + '</nav>' for L, cs in groups.items())
    js = "<script>document.getElementById('q').addEventListener('input',function(){var v=this.value.toLowerCase();document.querySelectorAll('.dir-list a').forEach(function(a){a.style.display=a.dataset.n.indexOf(v)>-1?'':'none'});});</script>"
    desc = f'Directory of all {len(cities)} incorporated cities in Oregon with county, 2020 Census population, history, and moving guides.'
    cities_ld = ld({'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'Oregon Cities A-Z', 'description': desc,
                    'url': f'{BASE_URL}/cities/', 'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(cities)}})
    return (head('Oregon Cities A–Z | All 241 Incorporated Cities', desc, '/cities/', extra=cities_ld, up='../') + header('../') + ticker_html() + alert_banner()
            + f'<div class="hero"><div class="wrap"><h1>Oregon Cities A&ndash;Z</h1><p>Every incorporated city in Oregon ({len(cities)} total), with county and 2020 Census population.</p></div></div>'
            + f'<main><div class="wrap"><nav class="crumbs"><a href="../index.html">Home</a> &rsaquo; Oregon Cities</nav><p style="margin:18px 0 8px"><input id="q" type="search" placeholder="Filter by city or county name..." aria-label="Filter cities"></p>'
            + f'<nav class="alpha">{alpha}</nav>{body}</div></main>' + js + footer('../', '<br>Population: U.S. Census Bureau 2020.'))


def simple_page(path, title, desc, h1, sub, body, page_type='WebPage'):
    page_ld = ld({'@context': 'https://schema.org', '@type': page_type, 'name': title, 'description': desc, 'url': f'{BASE_URL}{path}',
                  'isPartOf': {'@type': 'WebSite', 'name': 'Oregon Information', 'url': f'{BASE_URL}/'}})
    return (head(title, desc, path, extra=page_ld, up='../') + header('../') + ticker_html() + alert_banner()
            + f'<div class="hero"><div class="wrap"><h1>{h1}</h1><p>{sub}</p></div></div>'
            + f'<main><div class="wrap prose"><nav class="crumbs"><a href="../index.html">Home</a> &rsaquo; {h1}</nav>{body}</div></main>' + footer('../'))


ABOUT = f'''<h2 class="st">What Oregon Information is</h2>
<p>Oregon Information is an independent, free guide to the State of Oregon. It brings together practical facts about all 241 incorporated cities and all 36 counties &mdash; population, history, location, official websites &mdash; along with step-by-step guides for people <a href="../moving-to-oregon/index.html">moving to Oregon</a> and people <a href="../visit-oregon/index.html">visiting</a>.</p>
<h2 class="st">Who it is for</h2>
<p>Newcomers comparing places to live, visitors planning a trip, and Oregonians who want a quick, plain-language starting point before contacting a city, county or state office.</p>
<h2 class="st">Where the information comes from</h2>
<ul style="padding-left:20px">
<li>Population figures: U.S. Census Bureau (2010 and 2020 decennial census).</li>
<li>City and county background, incorporation dates, coordinates and photos: Wikipedia, Wikidata and Wikimedia Commons, used under their Creative Commons licenses with attribution on each page.</li>
<li>Government services and programs: official State of Oregon websites, linked directly.</li>
</ul>
<p>We check sources carefully, but details such as utility providers, school assignments and office hours change. Always confirm with the official agency before making decisions.</p>
<h2 class="st">Independence</h2>
<p>Oregon Information is not affiliated with, endorsed by, or operated by the State of Oregon or any city or county government.</p>
<h2 class="st">Corrections and suggestions</h2>
<p>Spotted something out of date? Please <a href="../contact/index.html">contact us</a> &mdash; corrections are welcome and appreciated.</p>'''

CONTACT = f'''<h2 class="st">Get in touch</h2>
<p>Questions, corrections, or suggestions for a city or county page? Email us at <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>. We read every message and aim to reply within a few business days.</p>
<h2 class="st">Reporting a correction</h2>
<p>To help us fix things quickly, please include the page address (URL), what is wrong, and a link to an official source if you have one.</p>
<h2 class="st">Need government help?</h2>
<p>Oregon Information is an independent website and cannot process applications or access government records. For official help:</p>
<ul style="padding-left:20px">
<li><a href="https://www.oregon.gov/" target="_blank" rel="noopener">Oregon.gov</a> &mdash; state agencies</li>
<li><a href="https://www.oregon.gov/odot/dmv/" target="_blank" rel="noopener">Oregon DMV</a></li>
<li><a href="https://one.oregon.gov/" target="_blank" rel="noopener">ONE Oregon</a> &mdash; Oregon Health Plan, SNAP and cash assistance</li>
<li><a href="https://www.211info.org/" target="_blank" rel="noopener">211info</a> &mdash; dial 2-1-1 for local resources</li>
</ul>'''

PRIVACY = f'''<p><em>Last updated: {date.today().strftime("%B %-d, %Y")}</em></p>
<h2 class="st">Summary</h2>
<p>Oregon Information is a read-only informational website. We do not require accounts, we do not sell personal information, and we do not run advertising trackers.</p>
<h2 class="st">Information collected automatically</h2>
<p>Like nearly all websites, our hosting provider and content-delivery/security service (Cloudflare) automatically record standard technical data when you visit &mdash; such as your IP address, browser type, the page requested, and the date and time. This data is used to deliver the site, keep it secure, and understand overall traffic. Cloudflare may set strictly necessary security cookies.</p>
<h2 class="st">Information you send us</h2>
<p>If you email us, we receive your email address and whatever you include in your message. We use it only to reply and to improve the site, and we do not share it.</p>
<h2 class="st">Analytics</h2>
<p>If we add a privacy-respecting analytics tool in the future (for example, Google Analytics), it will be used only to measure aggregate traffic, and this policy will be updated to say so.</p>
<h2 class="st">Third-party links and images</h2>
<p>Pages link to government agencies and other external websites, and some photos are loaded from Wikimedia Commons. Those sites have their own privacy policies, which we do not control.</p>
<h2 class="st">Children</h2>
<p>This site is intended for a general audience and does not knowingly collect information from children under 13.</p>
<h2 class="st">Changes and contact</h2>
<p>We may update this policy; the date above shows the latest revision. Questions? Email <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>'''


def big_region(city):
    """Return the 7-region name for a city dict."""
    county = city['counties'][0]
    sub = COUNTY_INFO.get(county, ('Unknown',))[0]
    return BIG_REGION_MAP.get(sub, 'Oregon')


def region_page(rname, rcities):
    rc = REGION_CONTENT[rname]
    rslug = REGION_SLUGS[rname]
    path = f'/regions/{rslug}/'
    desc = rc['desc']
    meta_desc = (f"{rname} guide: {len(rcities)} cities across {len(REGION_COUNTIES[rname])} counties. "
                 f"Population, living, visiting and travel information for every {rname} city.")
    counties_list = REGION_COUNTIES[rname]
    evoke = REGION_THEME.get(rname, ('', '', ''))[2]
    total_pop = sum(int(float(c['pop2020'] or 0)) for c in rcities)
    r_kw = f"{rname} Oregon, {rname} cities, living in {rname}, visiting {rname}, " + ', '.join(f'{cn} County Oregon' for cn in REGION_COUNTIES[rname]) + ', Oregon regions'
    counties_html = ', '.join(f'<a href="../../counties/{slug(cn)}/index.html">{e(cn)} County</a>' for cn in counties_list)
    sorted_cities = sorted(rcities, key=lambda c: -float(c['pop2020'] or 0))
    top = sorted_cities[:18]
    cities_grid = ''.join(
        f'<a href="../../cities/{slug(c["name"])}/index.html">{e(c["name"])}'
        f'<small>{e(c["counties"][0])} Co. &middot; pop. {n(c["pop2020"])}</small></a>' for c in top)
    all_rows = ''.join(
        f'<tr><td><a href="../../cities/{slug(c["name"])}/index.html">{e(c["name"])}</a></td>'
        f'<td>{e(", ".join(c["counties"]))}</td><td>{n(c["pop2020"])}</td></tr>' for c in sorted_cities)
    highlights_html = ''.join(f'<li style="padding:4px 0">{e(h)}</li>' for h in rc['highlights'])
    ld_obj = {'@context':'https://schema.org','@type':'Place','name':f'{rname}, Oregon','url':f'{BASE_URL}{path}',
              'containedInPlace':{'@type':'State','name':'Oregon'}}
    bread = {'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[
        {'@type':'ListItem','position':1,'name':'Home','item':f'{BASE_URL}/'},
        {'@type':'ListItem','position':2,'name':'Oregon Regions','item':f'{BASE_URL}/regions/'},
        {'@type':'ListItem','position':3,'name':rname,'item':f'{BASE_URL}{path}'}]}
    return (head(f'{rname}: {len(rcities)} Cities, Living & Travel Guide', meta_desc, path, 'article', None, ld(ld_obj)+ld(bread), '../../', r_kw)
            + header('../../') + ticker_html() + alert_banner()
            + f'<div class="hero region-hero"{hero_style(rname)}>{oregon_silhouette()}<div class="wrap"><h1>{e(rname)}, Oregon</h1>'
            + f'<p class="city-tagline">{e(evoke)}</p><p class="hero-sub">{e(rc["hero_sub"])}</p>'
            + f'<div class="pills"><span class="pill">&#127961; {len(rcities)} cities</span><span class="pill">&#127963; {len(counties_list)} counties</span>'
            + f'<span class="pill">&#128101; {total_pop:,} residents (2020)</span></div></div></div>'
            + f'<main><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><a href="../../index.html">Home</a> &rsaquo; <a href="../index.html">Oregon Regions</a> &rsaquo; {e(rname)}</nav>'
            + f'<h2 class="st">About the {e(rname)} Region</h2><section class="prose"><p>{e(desc)}</p></section>'
            + f'<h2 class="st">Counties</h2><p class="prose" style="margin:8px 0 24px">{counties_html}</p>'
            + f'<h2 class="st">Highlights</h2><ul style="padding-left:20px;margin:0 0 24px">{highlights_html}</ul>'
            + f'<h2 class="st">Living in {e(rname)}</h2><section class="prose"><p>{e(rc["living"])}</p></section>'
            + f'<h2 class="st">Visiting {e(rname)}</h2><section class="prose"><p>{e(rc["visiting"])}</p></section>'
            + f'<h2 class="st">Top Cities in {e(rname)}</h2><nav class="dir-list">{cities_grid}</nav>'
            + f'<h2 class="st">All Cities in {e(rname)} ({len(sorted_cities)} total)</h2>'
            + f'<table class="tbl"><tr><th>City</th><th>County</th><th>Population (2020)</th></tr>{all_rows}</table>'
            + '<p class="back"><a href="../index.html">&larr; All Oregon Regions</a></p></div></main>'
            + footer('../../'))


def regions_index(all_cities):
    path = '/regions/'
    desc = ("Explore Oregon's 7 regions: Portland Metro, Willamette Valley, the Coast, the Gorge, and Central, Eastern and "
            "Southern Oregon, with city and travel guides.")
    region_cards = ''
    for rname, rslug2 in REGION_SLUGS.items():
        rc = REGION_CONTENT[rname]
        city_count = sum(1 for c in all_cities if big_region(c) == rname)
        ra, rb, _ = REGION_THEME[rname]
        region_cards += (f'<a href="{rslug2}/index.html" style="display:block;text-decoration:none;color:inherit;border-top-color:{rb}" class="card">'
                         f'<h3>{e(rname)}</h3>'
                         f'<p style="font-size:.92rem;color:var(--tx);margin:6px 0">{e(rc["desc"][:150])}&hellip;</p>'
                         f'<p style="font-size:.84rem;color:var(--mu);margin-top:6px">{city_count} cities &middot; {len(REGION_COUNTIES[rname])} counties</p>'
                         f'</a>')
    ld_obj = {'@context':'https://schema.org','@type':'ItemList','name':'Oregon Regions',
              'url':f'{BASE_URL}{path}','numberOfItems':7}
    return (head("Oregon's 7 Regions: Coast, Valley, Gorge, Central & More", desc, path, 'website', None, ld(ld_obj), '../',
                 'Oregon regions, Portland Metro, Willamette Valley, Oregon Coast, Columbia River Gorge, Central Oregon, Eastern Oregon, Southern Oregon, Oregon cities by region')
            + header('../') + ticker_html() + alert_banner()
            + f'<div class="hero region-hero">{oregon_silhouette()}<div class="wrap"><h1>Oregon&rsquo;s Seven Regions</h1>'
            + '<p>Explore Oregon by region &mdash; cities, counties, living guides, and things to do in each part of the state.</p></div></div>'
            + f'<main><div class="wrap"><nav class="crumbs"><a href="../index.html">Home</a> &rsaquo; Oregon Regions</nav>'
            + f'<div class="cards" style="margin-top:24px">{region_cards}</div>'
            + '</div></main>' + footer('../'))


def oregon_page():
    path = '/oregon/'
    title = 'Oregon State Guide: Facts, Population, Cities & Counties'
    desc = ('Guide to the State of Oregon: population, capital, state symbols, geography, history and economy, '
            'plus all 241 cities, 36 counties and 7 regions.')
    kw = ('Oregon, State of Oregon, Oregon facts, Oregon population, Oregon cities, Oregon counties, Oregon regions, '
          'moving to Oregon, visiting Oregon, Oregon state symbols, Oregon history')
    facts_rows = ''.join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in OREGON_FACTS)
    ld_obj = {'@context':'https://schema.org','@type':'State','name':'Oregon','url':f'{BASE_URL}{path}'}
    bread = {'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[
        {'@type':'ListItem','position':1,'name':'Home','item':f'{BASE_URL}/'},
        {'@type':'ListItem','position':2,'name':'Oregon State Facts','item':f'{BASE_URL}{path}'}]}
    region_links = ''.join(
        f'<a href="/regions/{REGION_SLUGS[r]}/index.html" style="display:block;text-decoration:none;color:inherit" class="card">'
        f'<h3>{e(r)}</h3><p style="font-size:.92rem;color:var(--tx);margin:4px 0">{e(REGION_CONTENT[r]["desc"][:120])}&hellip;</p></a>'
        for r in REGION_SLUGS)
    return (head(title, desc, path, 'article', None, ld(ld_obj)+ld(bread), '../', kw)
            + header('../') + ticker_html() + alert_banner()
            + f'<div class="or-hero">{oregon_silhouette(cls="or-sil or-sil-lg")}<div class="wrap">'
            + '<p class="or-eyebrow">&#10022; The Beaver State &middot; Est. 1859 &#10022;</p>'
            + '<h1>Your Complete Guide to the State of Oregon</h1>'
            + '<p class="or-sub">Explore 241 cities, 36 counties, 7 regions &mdash; population data, schools, utilities, attractions &amp; more</p>'
            + '<p class="or-cta"><a class="btn-cta" href="/cities/">Explore Oregon &rarr;</a><a class="btn-ghost" href="/regions/">Browse the 7 regions</a></p>'
            + '</div></div>'
            + f'<main><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><a href="../index.html">Home</a> &rsaquo; Oregon State Facts</nav>'
            + f'<h2 class="st">Quick Facts</h2><section class="facts"><table>{facts_rows}</table></section>'
            + '''<h2 class="st">About Oregon</h2><section class="prose">
<p>Oregon is a U.S. state in the Pacific Northwest, bordered by Washington to the north, Idaho to the east, Nevada and California to the south, and the Pacific Ocean to the west. It became the 33rd state on February&nbsp;14, 1859 &mdash; a date commemorated as Oregon Statehood Day.</p>
<p>Oregon is geographically diverse: the wet, temperate west side of the Cascades contrasts sharply with the dry, high-desert east side. The Cascade Range runs north&ndash;south through the state, and the Coast Range parallels the Pacific shore. Major rivers include the Columbia (northern border), the Willamette (through the most populated areas), and the Rogue, Deschutes, McKenzie, and John Day rivers.</p>
<p>The state&rsquo;s population is concentrated in the <a href="/regions/willamette-valley/index.html">Willamette Valley</a> and <a href="/regions/portland-metro/index.html">Portland Metro</a> area, which together hold more than two-thirds of all Oregonians. Portland is by far the largest city; Salem (the capital), Eugene, Gresham, Hillsboro, and Beaverton round out the six most populous cities.</p>
</section>'''
            + '''<h2 class="st">Economy</h2><section class="prose">
<p>Oregon&rsquo;s economy is anchored by technology, agriculture, timber, food processing, and tourism. The tech sector &mdash; led by Intel, Nike, Adidas, and many firms clustered in Washington County&rsquo;s &ldquo;Silicon Forest&rdquo; &mdash; accounts for a large share of exports. Healthcare (Providence, Oregon Health &amp; Science University, Asante) is a major employer statewide.</p>
<p>Agriculture thrives in the Willamette Valley (wine grapes, berries, hazelnuts, Christmas trees), the Rogue Valley (pears, wine grapes), and Eastern Oregon (wheat, cattle, potatoes). Oregon&rsquo;s timber industry, though smaller than its historical peak, remains important in rural counties. Tourism draws millions of visitors to the coast, Crater Lake, Mt.&nbsp;Hood, and the Columbia River Gorge.</p>
<p>Oregon has <strong>no statewide sales tax</strong>, which affects consumer prices and cross-border shopping patterns. The state does levy a personal income tax.</p>
</section>'''
            + '''<h2 class="st">History</h2><section class="prose">
<p>Oregon&rsquo;s pre-contact history spans thousands of years of Indigenous settlement. Nations including the Chinook, Kalapuya, Nez Perce, Paiute, Tillamook, Coos, and many others lived throughout the region. European contact began in the 18th century through maritime exploration; Lewis and Clark reached the Pacific here in 1805 and wintered at Fort Clatsop near present-day Astoria.</p>
<p>The Oregon Trail &mdash; one of the great mass migrations in American history &mdash; brought roughly 400,000 settlers from Missouri to Oregon between the 1840s and 1860s. Statehood followed on February&nbsp;14, 1859. The 20th century brought significant industrialization, construction of Columbia River hydroelectric dams, World War II shipbuilding in Portland, and postwar suburban growth across the Willamette Valley.</p>
</section>'''
            + f'<h2 class="st">Explore Oregon by Region</h2><div class="cards">{region_links}</div>'
            + '<h2 class="st">Explore by County or City</h2><div class="cards">'
            + '<a href="/counties/index.html" class="card" style="display:block;text-decoration:none;color:inherit"><h3>All 36 Counties</h3><p style="font-size:.92rem;color:var(--tx)">Population, history, and cities for every Oregon county.</p></a>'
            + '<a href="/cities/index.html" class="card" style="display:block;text-decoration:none;color:inherit"><h3>All 241 Cities A&ndash;Z</h3><p style="font-size:.92rem;color:var(--tx)">Directory of every incorporated city in Oregon with facts and moving guides.</p></a>'
            + '</div>'
            + '<p class="back"><a href="../index.html">&larr; Home</a></p></div></main>'
            + footer('../'))


def write(path, content):
    for bad, good in LINK_FIXES.items():
        content = content.replace(f'href="{bad}"', f'href="{good}"').replace(f'href="{e(bad)}"', f'href="{e(good)}"')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f: f.write(content)


def main():
    cities = json.load(open('data/cities.json', encoding='utf-8'))
    counties = json.load(open('data/counties.json', encoding='utf-8'))
    custom = json.load(open('custom_city_content.json', encoding='utf-8')) if os.path.exists('custom_city_content.json') else {}
    for c in cities: c['counties'] = [x.strip() for x in c['county'].split(',')]
    for c in cities + counties:
        if c.get('website'): c['website'] = fix_url(c['website'])
    for k in counties: COUNTY_SITES[k['name']] = k.get('website', '')
    for c in cities:
        write(f'{OUT}/cities/{slug(c["name"])}/index.html', city_page(c, cities, custom))
    for k in counties:
        write(f'{OUT}/counties/{slug(k["name"])}/index.html', county_page(k, cities))
    write(f'{OUT}/cities/index.html', cities_index(cities))
    write(f'{OUT}/about/index.html', simple_page('/about/', 'About Oregon Information | Independent Oregon Guide', 'About Oregon Information: an independent, free guide to every Oregon city and county, with moving and visiting guides.', 'About Oregon Information', 'An independent, plain-language guide to the State of Oregon.', ABOUT, 'AboutPage'))
    write(f'{OUT}/contact/index.html', simple_page('/contact/', 'Contact Oregon Information', 'Contact Oregon Information with questions, corrections, or suggestions.', 'Contact Us', 'Questions, corrections and suggestions are always welcome.', CONTACT, 'ContactPage'))
    write(f'{OUT}/privacy/index.html', simple_page('/privacy/', 'Privacy Policy | Oregon Information', 'Privacy policy for oregoninformation.com: what information we collect, how cookies and analytics are used, and your choices.', 'Privacy Policy', 'How oregoninformation.com handles information.', PRIVACY))
    # Build 7 region pages + regions index
    for c in cities: c['counties'] = [x.strip() for x in c['county'].split(',')]  # ensure counties set (idempotent)
    by_region = {}
    for c in cities:
        r = big_region(c)
        by_region.setdefault(r, []).append(c)
    for rname in REGION_SLUGS:
        rslug2 = REGION_SLUGS[rname]
        write(f'{OUT}/regions/{rslug2}/index.html', region_page(rname, by_region.get(rname, [])))
    write(f'{OUT}/regions/index.html', regions_index(cities))
    # Oregon state facts page
    write(f'{OUT}/oregon/index.html', oregon_page())
    # Sitemap
    urls = ['/', '/oregon/', '/regions/', '/cities/', '/counties/', '/moving-to-oregon/', '/visit-oregon/', '/about/', '/contact/', '/privacy/']
    urls += [f'/regions/{REGION_SLUGS[r]}/' for r in REGION_SLUGS]
    urls += [f'/counties/{slug(k["name"])}/' for k in counties] + [f'/cities/{slug(c["name"])}/' for c in cities]
    if os.path.exists('data/blog_articles.json'):   # statewide blog (built by build_blog_index.py)
        urls += ['/blog/'] + [f'/blog/{a["slug"]}/' for a in json.load(open('data/blog_articles.json', encoding='utf-8'))]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += '\n'.join(f'  <url><loc>{BASE_URL}{u}</loc><lastmod>{TODAY}</lastmod></url>' for u in urls) + '\n</urlset>\n'
    write(f'{OUT}/sitemap.xml', sm)
    write(f'{OUT}/robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n')
    print(f'Built {len(cities)} city pages, {len(counties)} county pages, {len(REGION_SLUGS)} region pages + index, Oregon page, cities index, about/contact/privacy, sitemap ({len(urls)} URLs).')


if __name__ == '__main__':
    main()
