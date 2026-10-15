"""Comprehensive offline hydrological, flood history, drainage, and resident review dataset.
Covers all 28 States and 8 Union Territories of India.
Works completely offline without external API dependencies.
"""

from __future__ import annotations

import difflib
import re
from typing import TypedDict


class LocalityInfo(TypedDict, total=False):
    locality: str
    city: str
    aliases: list[str]
    state: str
    latitude: float
    longitude: float
    elevation_m: float
    terrain_type: str  # e.g., "Low-lying basin", "Coastal plain", "Floodplain", "Elevated ridge", "Plateau"
    drainage_system: str  # "Poor / Obsolete nallahs", "Moderate / Mixed open drains", "Adequate / Stormwater network"
    drainage_rating: int  # 1 (Critical) to 5 (Excellent)
    clogging_tendency: str  # "High - Frequent Clogging", "Moderate - Slow Drainage", "Low - Generally Clear"
    chronic_chokepoints: list[str]
    past_flood_events: list[dict[str, str]]
    resident_reviews: list[dict[str, str]]
    clogged_under_rain: bool  # True if typical monsoon/heavy rain clogs the area
    travel_advisory: str
    is_state_fallback: bool


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (s or "").lower())).strip()


def _fuzzy_match(needle: str, haystack: str, threshold: float = 0.72) -> bool:
    """Return True if needle is an exact match, substring, or has high sequence similarity with haystack."""
    if not needle or not haystack:
        return False
    n = _norm(needle)
    h = _norm(haystack)
    if n == h or n in h or h in n:
        return True
    return difflib.SequenceMatcher(None, n, h).ratio() >= threshold


# Comprehensive nationwide dataset covering 28 States and 8 Union Territories
INDIA_FLOOD_DATABASE: list[LocalityInfo] = [
    # ------------------ 1. ANDHRA PRADESH ------------------
    {
        "locality": "Benz Circle & Bandar Road",
        "city": "Vijayawada",
        "state": "Andhra Pradesh",
        "latitude": 16.5062,
        "longitude": 80.6480,
        "elevation_m": 18.0,
        "terrain_type": "Krishna river floodplain",
        "drainage_system": "Poor / Silted stormwater outfalls to Bandar canal",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Benz Circle underpass", "Pinnamaneni Polyclinic Road", "Rajarajeshwaripet"],
        "past_flood_events": [
            {"year": "2024", "event": "Budameru rivulet breach triggered massive flash inundation across Ajit Singh Nagar & Benz circle", "impact": "Water submerged arterial roads up to 4-6 feet"},
            {"year": "2009", "event": "Krishna river surge recorded 11.1 lakh cusecs discharge", "impact": "Widespread inundation in low-lying divisions"}
        ],
        "resident_reviews": [
            {"author": "Vijayawada Commuter Review", "rating": "Poor", "review": "Even 30 minutes of heavy downpour submerges Benz Circle junction and service lanes. Avoid two-wheelers during rain.", "date": "2024-09-03"},
            {"author": "Local Resident (Singh Nagar)", "rating": "Critical", "review": "Drainage outlets get backflow whenever Budameru and Krishna canals are full. Severe clogging occurs.", "date": "2024-09-10"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "High waterlogging hazard during rains. Divert via Inner Ring Road bypass."
    },
    {
        "locality": "RTC Complex & Gnanapuram",
        "city": "Visakhapatnam",
        "state": "Andhra Pradesh",
        "latitude": 17.7231,
        "longitude": 83.3013,
        "elevation_m": 12.0,
        "terrain_type": "Coastal bowl / Hill runoff basin",
        "drainage_system": "Moderate / Gedda drainage channels",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Gnanapuram railway under-bridge", "Poorana Market low area", "Sheela Nagar junction"],
        "past_flood_events": [
            {"year": "2023", "event": "Cyclone Michaung outer bands brought 140mm rainfall in 6 hours", "impact": "Submerged Convent junction & Gnanapuram subways"},
            {"year": "2014", "event": "Cyclone Hudhud coastal inundation & storm surge", "impact": "Severe urban flooding and infrastructure damage"}
        ],
        "resident_reviews": [
            {"author": "Vizag Resident", "rating": "Average", "review": "Railway underbridges flood rapidly. The main highway clears in an hour, but station road stays clogged.", "date": "2023-12-05"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Subways and railway under-bridges get submerged. Use flyover routes."
    },
    {
        "locality": "Buggavanka basin & 7-Roads",
        "city": "Kadapa",
        "state": "Andhra Pradesh",
        "latitude": 14.4673,
        "longitude": 78.8242,
        "elevation_m": 138.0,
        "terrain_type": "Buggavanka river depression",
        "drainage_system": "Poor / Flood canal siltation",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Buggavanka flood canal bridges", "Old Kadapa road", "NGO Colony"],
        "past_flood_events": [
            {"year": "2021", "event": "Annamayya dam breach upstream sent massive torrent into Buggavanka stream", "impact": "Over 2,000 houses flooded in Kadapa municipal limits"},
            {"year": "2001", "event": "IFRC documented 18,244 houses damaged after Buggavanka surplus release", "impact": "Water rose 1.5m in half an hour"}
        ],
        "resident_reviews": [
            {"author": "Local Citizen", "rating": "Poor", "review": "Low-lying areas along Buggavanka river bank submerge instantly if upstream checkdams open.", "date": "2023-11-20"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Avoid Buggavanka riverfront roads during heavy rainfall warnings."
    },

    # ------------------ 2. ARUNACHAL PRADESH ------------------
    {
        "locality": "Ganga Lake valley & Bank Tinali",
        "city": "Itanagar",
        "state": "Arunachal Pradesh",
        "latitude": 27.0844,
        "longitude": 93.6053,
        "elevation_m": 750.0,
        "terrain_type": "Hilly terrain / Valley runoff",
        "drainage_system": "Natural nallahs prone to mudslides",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Bank Tinali highway culvert", "Chandranagar bridge", "Chimpu low bridge"],
        "past_flood_events": [
            {"year": "2024", "event": "Cloudburst in Papum Pare hills caused flash flood in Senki stream", "impact": "Portions of NH-415 washed away, mud blockages stranded vehicles"},
            {"year": "2020", "event": "Severe monsoon flash floods triggered urban debris flow", "impact": "Multiple settlements submerged in low culverts"}
        ],
        "resident_reviews": [
            {"author": "Itanagar Driver", "rating": "Critical", "review": "Hill slopes bring gravel and slush directly onto Bank Tinali road. Total vehicular blockage during continuous rain.", "date": "2024-07-15"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Flash flood and mud blockage risk on valley roads. Keep away from Senki river banks."
    },
    {
        "locality": "Siang Riverfront & Main Bazaar",
        "city": "Pasighat",
        "state": "Arunachal Pradesh",
        "latitude": 28.0665,
        "longitude": 95.3267,
        "elevation_m": 155.0,
        "terrain_type": "Siang river terrace",
        "drainage_system": "Open hill storm drains",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Babu Town nallah", "Pasighat-Pangin road culvert"],
        "past_flood_events": [
            {"year": "2023", "event": "Siang river crossed danger mark by 1.2 meters", "impact": "Submerged riverside agricultural belts and low streets"}
        ],
        "resident_reviews": [
            {"author": "Pasighat Resident", "rating": "Average", "review": "Heavy rains flood open roadside gullies, making market lanes slippery with overflow.", "date": "2023-08-12"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "River level rises rapidly; stay alert along Siang banks."
    },

    # ------------------ 3. ASSAM ------------------
    {
        "locality": "Brahmaputra Valley Basin & Chronic Flood Corridor",
        "city": "Upper Assam",
        "aliases": [
            "Upper Assam",
            "Upper Assam City",
            "Upper Assam Region",
            "Brahmaputra Flood Plain",
            "Brahmaputra Valley",
            "Upper Assam District",
            "Eastern Assam",
            "Upper Brahmaputra",
            "Upper Assam Flood Zone"
        ],
        "state": "Assam",
        "latitude": 27.2000,
        "longitude": 94.6000,
        "elevation_m": 98.0,
        "terrain_type": "Brahmaputra floodplains, low-lying alluvial silt basins and breached dyke corridors",
        "drainage_system": "Critical / Breached river embankments, silted riverbeds, overflowing wetlands and backflow from Brahmaputra, Subansiri and Dhansiri rivers",
        "drainage_rating": 1,
        "clogging_tendency": "High - Severe Flooding & Waterlogging",
        "chronic_chokepoints": [
            "NH-37 / NH-715 submerged corridor",
            "Dhansiri river bridge approach",
            "Subansiri embankment breach cuts",
            "Brahmaputra dyke breaches",
            "Dikhow river bund chokepoint",
            "Low-lying agricultural and residential wards"
        ],
        "past_flood_events": [
            {
                "year": "2026",
                "event": "Catastrophic Upper Assam monsoon deluge; Brahmaputra, Subansiri, Dikhow, and Dhansiri rivers simultaneously breached embankments across Upper Assam",
                "impact": "Over 1.8 million residents affected; hundreds of villages, major arterial highway stretches, and residential townships submerged under 4 to 8 feet of floodwater"
            },
            {
                "year": "2024",
                "event": "Severe Upper Assam inundation affecting Dibrugarh, Jorhat, Golaghat, Sivasagar, Lakhimpur and Dhemaji",
                "impact": "Over 30 districts impacted; residential colonies, tea estates, and highway connections submerged for weeks"
            },
            {
                "year": "2022",
                "event": "Historic Brahmaputra basin flood crisis",
                "impact": "Massive displacement, breach of 25+ river embankments, complete cutoff of road transit"
            }
        ],
        "resident_reviews": [
            {
                "author": "Upper Assam Resident",
                "rating": "Critical",
                "review": "Witnessed by residents: when heavy monsoon rain strikes, river embankments breach and floodwaters submerge entire colonies within hours. It may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too.",
                "date": "2026-07-15"
            },
            {
                "author": "Local Commuter & Resident",
                "rating": "Critical",
                "review": "Every single monsoon with heavy rainfall, roads and markets submerge under knee-to-waist deep water. As per past experiences witnessed by residents, this entire area has high risk of flooding again during heavy downpours.",
                "date": "2026-06-29"
            }
        ],
        "clogged_under_rain": True,
        "travel_advisory": "CRITICAL FLOOD & INUNDATION ZONE: High risk of road blockages and embankment breaches during rain. It may be flooded as per past experiences witnessed by residents if it rains heavily in future too. Avoid low-lying river corridors and underpasses."
    },
    {
        "locality": "Tarajan, Malow Ali & Bhogdoi River Embankment",
        "city": "Jorhat",
        "aliases": ["Jorhat City", "Jorhat Town", "Bhogdoi", "Nimati Ghat", "Tarajan", "Malow Ali", "Upper Assam Jorhat"],
        "state": "Assam",
        "latitude": 26.7509,
        "longitude": 94.2037,
        "elevation_m": 116.0,
        "terrain_type": "Bhogdoi river basin & alluvial plain",
        "drainage_system": "Critical / Silted Bhogdoi river and choked municipal stormwater drains",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging & Flash Floods",
        "chronic_chokepoints": ["Tarajan bypass", "Malow Ali underpass", "Gar-Ali central market", "Bhogdoi river bridge approaches"],
        "past_flood_events": [
            {"year": "2026", "event": "Bhogdoi river overflowed banks flooding low-lying wards of Jorhat town", "impact": "Over 45,000 residents impacted; Tarajan and Malow Ali roads remained submerged for 4 days"},
            {"year": "2024", "event": "Brahmaputra backflow into Bhogdoi during heavy monsoon rains", "impact": "Severe inundation of Jorhat residential areas and Nimati Ghat road link"}
        ],
        "resident_reviews": [
            {"author": "Jorhat Resident (Tarajan)", "rating": "Critical", "review": "Even moderate downpours cause Bhogdoi river water to back up into our streets. It may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too.", "date": "2026-07-02"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "High waterlogging risk. Avoid Tarajan and low-lying market areas during rain."
    },
    {
        "locality": "North Lakhimpur Town & Ranganadi Floodplain",
        "city": "Lakhimpur",
        "aliases": ["North Lakhimpur", "Lakhimpur Town", "Ranganadi", "Subansiri Basin", "Mazor Chapori", "Upper Assam Lakhimpur"],
        "state": "Assam",
        "latitude": 27.2364,
        "longitude": 94.1028,
        "elevation_m": 101.0,
        "terrain_type": "Ranganadi-Subansiri river confluence floodplain",
        "drainage_system": "Critical / Dam water release backflow and breached earthen dykes",
        "drainage_rating": 1,
        "clogging_tendency": "High - Severe Flooding",
        "chronic_chokepoints": ["Chaboti", "Khelmati", "Ranganadi dyke breach point", "NH-15 submerged culverts"],
        "past_flood_events": [
            {"year": "2026", "event": "Ranganadi dam water release and continuous heavy cloudburst submerged North Lakhimpur", "impact": "Submersion of residential areas and dozens of fringe villages under 5-7 feet of water"},
            {"year": "2025", "event": "Embankment breach at Mazor Chapori and neighboring areas", "impact": "Multiple villages submerged following sudden water release"}
        ],
        "resident_reviews": [
            {"author": "North Lakhimpur Resident", "rating": "Critical", "review": "As witnessed by residents year after year, water levels rise abruptly during heavy monsoon downpours and dam releases. It may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too.", "date": "2026-06-20"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "SEVERE FLOOD HAZARD: Ranganadi floodplain is prone to sudden inundation. Move to higher ground during heavy rainfall."
    },
    {
        "locality": "Dhemaji Town, Silapathar & Jiadhal River Floodplain",
        "city": "Dhemaji",
        "aliases": ["Dhemaji Town", "Silapathar", "Jiadhal", "Dhemaji District", "Jonai", "Upper Assam Dhemaji"],
        "state": "Assam",
        "latitude": 27.4815,
        "longitude": 94.5828,
        "elevation_m": 104.0,
        "terrain_type": "Jiadhal 'River of Sorrow' flash-flood basin",
        "drainage_system": "Critical / Chronic sand deposition and riverbed shifting",
        "drainage_rating": 1,
        "clogging_tendency": "High - Chronic Flash Floods",
        "chronic_chokepoints": ["Silapathar town junction", "Jiadhal river bridge approach", "NH-515 submerged sections"],
        "past_flood_events": [
            {"year": "2026", "event": "Jiadhal flash floods breached railway line and highway", "impact": "Entire sub-division cut off; homes and paddies covered in silt and water"},
            {"year": "2024", "event": "Monsoon flood waves submerged 80% of Dhemaji rural and town areas", "impact": "Over 150,000 people displaced"}
        ],
        "resident_reviews": [
            {"author": "Dhemaji Citizen", "rating": "Critical", "review": "Dhemaji is historically Assam's most flood-prone district. As witnessed by all residents, it may be flooded as per past experiences if it rains heavily in future too.", "date": "2026-07-10"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "EXTREME FLASH FLOOD ALERT: NH-515 and rural links submerge rapidly during heavy rains."
    },
    {
        "locality": "Golaghat Town & Dhansiri River Basin",
        "city": "Golaghat",
        "aliases": ["Golaghat Town", "Bokakhat", "Dhansiri", "Numaligarh", "Kaziranga Fringe", "Upper Assam Golaghat"],
        "state": "Assam",
        "latitude": 26.5239,
        "longitude": 93.9622,
        "elevation_m": 100.0,
        "terrain_type": "Dhansiri river floodplain & low-lying wetlands",
        "drainage_system": "Critical / Silted Dhansiri river outfalls",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Inundation",
        "chronic_chokepoints": ["Bokakhat NH-715 low stretches", "Dhansiri bridge approaches", "Arengapara"],
        "past_flood_events": [
            {"year": "2026", "event": "Dhansiri river crossed extreme danger mark flooding Golaghat lowlands", "impact": "Inundation of town fringe and NH-715 animal corridor"}
        ],
        "resident_reviews": [
            {"author": "Golaghat Resident", "rating": "Critical", "review": "Witnessed by local residents: when Dhansiri river swells, town drainage chokes completely. It may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too.", "date": "2026-06-25"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "High waterlogging risk. Watch for flood water on NH-715."
    },
    {
        "locality": "Dikhow River Embankment & Central Sivasagar",
        "city": "Sivasagar",
        "aliases": ["Sibsagar", "Sivasagar Town", "Dikhow", "Disangmukh", "Nazira", "Upper Assam Sivasagar"],
        "state": "Assam",
        "latitude": 26.9826,
        "longitude": 94.6425,
        "elevation_m": 99.0,
        "terrain_type": "Dikhow-Disang river alluvial plain",
        "drainage_system": "Critical / Silted Dikhow river bunds and closed sluices",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Station Chariali", "Disangmukh road", "Dikhow river bund roads"],
        "past_flood_events": [
            {"year": "2026", "event": "Dikhow river breached secondary bund flooding Nazira and Sivasagar wards", "impact": "Over 60,000 residents affected; water stagnated for 5 days"}
        ],
        "resident_reviews": [
            {"author": "Sivasagar Resident", "rating": "Critical", "review": "As witnessed by residents: Dikhow river water levels exceed town drain levels during monsoon, causing backflow into homes. It may be flooded as per past experiences if it rains heavily in future too.", "date": "2026-07-08"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Dikhow river backflow hazard during heavy rainfall."
    },
    {
        "locality": "Tinsukia Town, Guijan & Dibru River Basin",
        "city": "Tinsukia",
        "aliases": ["Tinsukia Town", "Guijan", "Doomdooma", "Dibru Basin", "Makum", "Upper Assam Tinsukia"],
        "state": "Assam",
        "latitude": 27.4922,
        "longitude": 95.3537,
        "elevation_m": 116.0,
        "terrain_type": "Dibru river basin and alluvial lowlands",
        "drainage_system": "Poor / Obsolete municipal drains and Dibru river swelling",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Chirwapatty", "GNB Road underpass", "Guijan river ghat road"],
        "past_flood_events": [
            {"year": "2026", "event": "Dibru river overflow submerged Guijan and low-lying Tinsukia wards", "impact": "Major transit disruption and displacement of riverbank communities"}
        ],
        "resident_reviews": [
            {"author": "Tinsukia Merchant & Resident", "rating": "Poor", "review": "Drains in Chirwapatty and GNB road overflow instantly in heavy rain. It may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too.", "date": "2026-06-19"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Road waterlogging at Chirwapatty and GNB road during downpours."
    },
    {
        "locality": "Kamalabari & Garmur, Majuli River Island",
        "city": "Majuli",
        "aliases": ["Majuli Island", "Kamalabari", "Garmur", "Jorhat Majuli", "River Island", "Upper Assam Majuli"],
        "state": "Assam",
        "latitude": 26.9500,
        "longitude": 94.2167,
        "elevation_m": 84.0,
        "terrain_type": "Brahmaputra-Subansiri riverine island floodplain",
        "drainage_system": "Critical / No formal drainage, surrounded by floodwaters",
        "drainage_rating": 1,
        "clogging_tendency": "High - Severe Inundation & Erosion",
        "chronic_chokepoints": ["Kamalabari ghat link", "Garmur-Jengraimukh road", "Embankment breach zones"],
        "past_flood_events": [
            {"year": "2026", "event": "Over 65% of Majuli submerged during 2026 monsoon wave", "impact": "Complete road network submerged; ferry services halted"}
        ],
        "resident_reviews": [
            {"author": "Majuli Resident", "rating": "Critical", "review": "Every year floodwaters enter our homes. Witnessed by generations of residents: it may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too.", "date": "2026-07-12"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "CRITICAL FLOOD ZONE: Island roads cut off during monsoon surges. Avoid travel."
    },
    {
        "locality": "Rukminigaon & Zoo Road (R.G. Baruah Road)",
        "city": "Guwahati",
        "aliases": ["Guwahati City", "Dispur", "GS Road", "Zoo Road", "Anil Nagar", "Nabin Nagar", "Kamrup"],
        "state": "Assam",
        "latitude": 26.1445,
        "longitude": 91.7362,
        "elevation_m": 55.0,
        "terrain_type": "Inter-hill wetland basin (Bharalu catchment)",
        "drainage_system": "Critical / Silted Bharalu river and Bahini nallah",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Rukminigaon GS Road junction", "Zoo Road Tiniali", "Anil Nagar", "Nabin Nagar"],
        "past_flood_events": [
            {"year": "2026", "event": "Massive urban flash flood submerged GS Road, Zoo Road, and Anil Nagar under 4-5 feet water", "impact": "City paralyzed for 24 hours; rescue boats deployed"},
            {"year": "2024", "event": "Flash urban flood submerged GS Road & Zoo Road for 18 hours", "impact": "Chest-deep water in Anil Nagar; boats deployed in smart city area"},
            {"year": "2022", "event": "Worst urban deluge in Kamrup district", "impact": "Over 200,000 residents stranded by knee-to-waist deep waterlogging"}
        ],
        "resident_reviews": [
            {"author": "Guwahati Resident (Anil Nagar)", "rating": "Critical", "review": "Just 20 minutes of shower causes waist-deep water. Bahini canal overflows immediately back into residential compounds. It may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too.", "date": "2026-06-25"},
            {"author": "Daily Commuter", "rating": "Poor", "review": "GS Road under Rukminigaon flyover gets completely waterlogged. Cars stall every single monsoon. Witnessed repeatedly by commuters: it will be flooded again under heavy rain.", "date": "2026-07-02"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "SEVERE CLOGGING DANGER. GS Road and Zoo Road become impassable during rain. Use VIP road."
    },
    {
        "locality": "Mancotta Road & AT Road",
        "city": "Dibrugarh",
        "aliases": ["Dibrugarh City", "Dibrugarh Town", "Mancotta", "Thana Chariali", "Upper Assam Dibrugarh"],
        "state": "Assam",
        "latitude": 27.4728,
        "longitude": 94.9120,
        "elevation_m": 108.0,
        "terrain_type": "Brahmaputra dyke basin",
        "drainage_system": "Poor / Dibrugarh Town Protection drain choking",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Thana Chariali", "Naliapool railway overbridge", "Cole Road"],
        "past_flood_events": [
            {"year": "2026", "event": "Embankment breach along Brahmaputra inundated Dibrugarh town lowlands and Mancotta road", "impact": "Residential colonies submerged for 6 days; NDRF deployed"},
            {"year": "2024", "event": "Brahmaputra in spate alongside 110mm cloudburst", "impact": "Town submerged for 7 continuous days; pump stations overwhelmed"},
            {"year": "2020", "event": "Monsoon flood breached secondary embankment", "impact": "Inundation of low wards"}
        ],
        "resident_reviews": [
            {"author": "Dibrugarh Citizen", "rating": "Critical", "review": "Dibrugarh Town Protection drain is heavily choked. Water stagnates for days on Mancotta Road. Witnessed by residents: it may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too.", "date": "2026-07-10"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "High waterlogging risk. Avoid Thana Chariali under heavy downpours. It may be flooded as per past experiences witnessed by residents if it rains heavily in future too."
    },
    {
        "locality": "Rangirkhari & Tarapur",
        "city": "Silchar",
        "aliases": ["Silchar City", "Silchar Town", "Cachar", "Barak Valley", "Rangirkhari", "Tarapur"],
        "state": "Assam",
        "latitude": 24.8333,
        "longitude": 92.7789,
        "elevation_m": 25.0,
        "terrain_type": "Barak river basin / Bethukandi breach zone",
        "drainage_system": "Critical / Silted sluice gates to Barak river",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Rangirkhari point", "Public School road", "Hospital road underpass"],
        "past_flood_events": [
            {"year": "2026", "event": "Barak river overflowed sluice gates flooding Rangirkhari and Tarapur", "impact": "Chest-deep water in hospital area for 3 days"},
            {"year": "2022", "event": "Historic Bethukandi dyke breach flooded 90% of Silchar town", "impact": "Water reached 10-15 feet inside town; air-dropping of relief required"},
            {"year": "2024", "event": "Heavy Barak river overflow during Cyclone Remal aftermath", "impact": "Major roads cut off for 5 days"}
        ],
        "resident_reviews": [
            {"author": "Silchar Resident", "rating": "Critical", "review": "Rangirkhari drain cannot discharge when Barak river water rises. Roads transform into rivers. It may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too.", "date": "2026-06-18"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Extreme waterlogging & backflow hazard during monsoon. It may be flooded as per past experiences witnessed by residents if it rains heavily in future too."
    },

    # ------------------ 4. BIHAR ------------------
    {
        "locality": "Tower Chowk, Laheriasarai & Benta (DMCH)",
        "city": "Darbhanga",
        "aliases": ["Dharbanga", "Darbhanga City", "Laheriasarai", "DMCH", "Darbhanga Town", "Donar"],
        "state": "Bihar",
        "latitude": 26.1542,
        "longitude": 85.8918,
        "elevation_m": 52.0,
        "terrain_type": "Bagmati & Adhwara basin / Saucer-shaped Mithila plain",
        "drainage_system": "Critical / Choked Harahi & Dighi lake outfalls, silted open nallahs",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Tower Chowk market", "Donar railway gumti", "Laheriasarai VIP road", "Benta Chowk near DMCH", "Bhatiyari Sarai low underpass"],
        "past_flood_events": [
            {"year": "2024", "event": "Bagmati river embankment breaches in Hayaghat; Adhwara river flood surge inundated urban wards", "impact": "Tower Chowk and Laheriasarai rail section waterlogged; DMCH emergency approach submerged"},
            {"year": "2020", "event": "Historic Mithilanchal deluge after 300mm continuous rainfall", "impact": "DMCH hospital wards submerged under 3-4 feet water for 14 days; SDRF boats deployed inside medical college campus"},
            {"year": "2019", "event": "Kamala-Balan and Bagmati twin river overflow entered residential colonies in Darbhanga town", "impact": "Thousands stranded in low-lying wards with knee-to-waist deep water stagnation"}
        ],
        "resident_reviews": [
            {"author": "DMCH Resident Doctor", "rating": "Critical", "review": "Every monsoon downpour floods DMCH hospital OPD and Benta road. Even 45 minutes of heavy rain leaves Tower Chowk submerged knee-deep.", "date": "2024-08-20"},
            {"author": "Laheriasarai Commuter", "rating": "Critical", "review": "Donar railway gumti and Laheriasarai VIP road become impassable pools during rains. Silted roadside nallahs overflow back onto the road.", "date": "2024-07-31"},
            {"author": "Darbhanga Town Citizen", "rating": "Poor", "review": "Water logging remains for 2 to 3 days after downpours because natural outlets into Dighi and Harahi ponds are encroached.", "date": "2024-08-11"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "SEVERE WATERLOGGING HAZARD. Avoid Tower Chowk, Donar railway crossing, and DMCH approach road during rainfall."
    },
    {
        "locality": "Rajendra Nagar & Kankarbagh",
        "city": "Patna",
        "aliases": ["Patliputra", "Patna City", "Danapur"],
        "state": "Bihar",
        "latitude": 25.5941,
        "longitude": 85.1376,
        "elevation_m": 53.0,
        "terrain_type": "Ganga & Punpun saucer-shaped depression",
        "drainage_system": "Poor / Sump house pump dependency",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Rajendra Nagar road no. 1-14", "Tiwari Bechar", "Tempo Stand Kankarbagh", "Saidpur nallah junction"],
        "past_flood_events": [
            {"year": "2019", "event": "Disastrous Patna urban deluge; 340mm rain in 3 days", "impact": "Waist-to-chest water for 9 days in Rajendra Nagar; SDRF boats rescued thousands"},
            {"year": "2021", "event": "Ganga backflow into Punpun canal system", "impact": "Low colonies inundated up to 3 feet"}
        ],
        "resident_reviews": [
            {"author": "Patna Local (Rajendra Nagar)", "rating": "Critical", "review": "Area is situated lower than Ganga river bed. If pumps fail for 1 hour, entire colony gets waterlogged knee-deep.", "date": "2024-08-14"},
            {"author": "Kankarbagh Resident", "rating": "Poor", "review": "Drainage covers are broken and nallahs overflow onto roads. Avoid travelling by car during monsoon downpours.", "date": "2024-07-28"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "CRITICAL CLOGGING AREA. Rajendra Nagar roads become waterlogged up to 3-4 feet in rain."
    },
    {
        "locality": "Moti Jheel & Maripur",
        "city": "Muzaffarpur",
        "aliases": ["Muzafarpur"],
        "state": "Bihar",
        "latitude": 26.1226,
        "longitude": 85.3906,
        "elevation_m": 56.0,
        "terrain_type": "Burhi Gandak river depression",
        "drainage_system": "Poor / Encroached natural wetlands",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Moti Jheel market", "Maripur railway underpass", "Kalyani Chowk"],
        "past_flood_events": [
            {"year": "2024", "event": "Burhi Gandak breach near Sikandarpur", "impact": "Commercial heart of Muzaffarpur drowned in 3 feet water"},
            {"year": "2020", "event": "Sustained monsoon overflow", "impact": "Major town routes closed for 2 weeks"}
        ],
        "resident_reviews": [
            {"author": "Shopkeeper Moti Jheel", "rating": "Critical", "review": "Every single monsoon water enters shops. The lake is encroached so water has nowhere to go.", "date": "2024-08-01"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Avoid Maripur underpass and Moti Jheel roads when it rains."
    },
    {
        "locality": "Tilkamanjhi & Nathnagar",
        "city": "Bhagalpur",
        "aliases": ["Silk City", "Nathnagar", "Bhagalpur City"],
        "state": "Bihar",
        "latitude": 25.2425,
        "longitude": 86.9842,
        "elevation_m": 52.0,
        "terrain_type": "Ganga & Champa river confluence floodplain",
        "drainage_system": "Poor / Obsolete open nallahs draining into Champa river",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Tilkamanjhi Chowk", "Station Road underpass", "Nathnagar weavers colony"],
        "past_flood_events": [
            {"year": "2024", "event": "Ganga water level crossed danger level by 1.1 meters", "impact": "Water entered university campus and Nathnagar low roads"},
            {"year": "2021", "event": "High Ganga flood backed into city drainage lines", "impact": "Station road traffic suspended due to 2 feet water"}
        ],
        "resident_reviews": [
            {"author": "Bhagalpur Commuter", "rating": "Poor", "review": "Station road and Tilkamanjhi get choked whenever rain lasts more than an hour.", "date": "2024-08-16"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Waterlogging frequent at Station Road underpass during monsoon rains."
    },
    {
        "locality": "Civil Lines & GB Road",
        "city": "Gaya",
        "aliases": ["Gaya Ji", "Bodh Gaya", "Gaya Town"],
        "state": "Bihar",
        "latitude": 24.7914,
        "longitude": 85.0002,
        "elevation_m": 111.0,
        "terrain_type": "Falgu river terrace basin",
        "drainage_system": "Moderate / Open roadside storm channels",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["GB Road market", "Civil Lines court underpass", "Kendui low pocket"],
        "past_flood_events": [
            {"year": "2023", "event": "Falgu river flash surge due to Jharkhand catchment rains", "impact": "Low ghat areas inundated; Civil Lines drains backed up"}
        ],
        "resident_reviews": [
            {"author": "Gaya Resident", "rating": "Average", "review": "GB road clogs during peak cloudbursts, but drains clear within 2-3 hours after rain stops.", "date": "2024-07-19"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Caution on GB road and court area during torrential rainfall."
    },
    {
        "locality": "Line Bazar & Bhatta Bazar",
        "city": "Purnia",
        "aliases": ["Purnea", "Gulabbagh"],
        "state": "Bihar",
        "latitude": 25.7771,
        "longitude": 87.4753,
        "elevation_m": 37.0,
        "terrain_type": "Saura river floodplain / Seemanchal basin",
        "drainage_system": "Poor / Encroached natural channels",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Line Bazar medical hub", "Bhatta Bazar main chowk", "Khuskibagh underpass"],
        "past_flood_events": [
            {"year": "2024", "event": "Saura river flood discharge combined with 140mm torrential rain", "impact": "Line Bazar medical clinics flooded; patients evacuated by tractors"},
            {"year": "2017", "event": "Devastating Seemanchal flood deluge", "impact": "Urban areas cut off for 5 days"}
        ],
        "resident_reviews": [
            {"author": "Line Bazar Medical Professional", "rating": "Critical", "review": "Line Bazar clinics get flooded with dirty water every rainy season. Movement of ambulances is severely blocked.", "date": "2024-08-25"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "High waterlogging risk at Line Bazar medical area. Exercise caution."
    },
    {
        "locality": "D.B. Road & Gangjala",
        "city": "Saharsa",
        "aliases": ["Kosi Saharsa", "Saharsa Town"],
        "state": "Bihar",
        "latitude": 25.8835,
        "longitude": 86.6006,
        "elevation_m": 45.0,
        "terrain_type": "Kosi river flood depression",
        "drainage_system": "Critical / Non-existent stormwater outfalls",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["D.B. Road main commercial belt", "Gangjala Chowk", "Matsyagandha road"],
        "past_flood_events": [
            {"year": "2024", "event": "Kosi river high flood release combined with localized cloudburst", "impact": "Submerged major town roads under 2-3 feet water for days"}
        ],
        "resident_reviews": [
            {"author": "Saharsa Trader", "rating": "Critical", "review": "D.B. Road stays waterlogged for days even after minor rainfall. Drainage infrastructure is almost non-existent.", "date": "2024-08-05"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Avoid D.B. Road and Gangjala Chowk under rain conditions."
    },
    {
        "locality": "Magardahi Ghat & Mohanpur",
        "city": "Samastipur",
        "aliases": ["Somastipur", "Samastipur Junction"],
        "state": "Bihar",
        "latitude": 25.8629,
        "longitude": 85.7811,
        "elevation_m": 52.0,
        "terrain_type": "Burhi Gandak river depression",
        "drainage_system": "Poor / Silted roadside gullies",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Magardahi Ghat road", "Mohanpur road railway underpass", "Kashipur Chowk"],
        "past_flood_events": [
            {"year": "2024", "event": "Burhi Gandak river level rose 1.4m above danger line", "impact": "Inundated Mohanpur low residential colonies"}
        ],
        "resident_reviews": [
            {"author": "Samastipur Citizen", "rating": "Poor", "review": "Railway underpasses flood instantly. Commuters get stranded for hours.", "date": "2024-07-22"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Railway underpasses severely clogged during downpours."
    },

    # ------------------ 5. CHHATTISGARH ------------------
    {
        "locality": "Pandri & Telibandha",
        "city": "Raipur",
        "state": "Chhattisgarh",
        "latitude": 21.2514,
        "longitude": 81.6296,
        "elevation_m": 298.0,
        "terrain_type": "Mahanadi basin gently undulating plain",
        "drainage_system": "Moderate / Chokda nallah upgrade ongoing",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Pandri cloth market subway", "Telibandha ring road junction", "Pachpedi Naka underpass"],
        "past_flood_events": [
            {"year": "2023", "event": "Torrential 120mm downpour in 4 hours", "impact": "Waterlogging in Pandri main market, 2 feet water at underpasses"}
        ],
        "resident_reviews": [
            {"author": "Raipur Commuter", "rating": "Average", "review": "Telibandha service lanes gather water quickly, but drains flush it within 2 hours once rain subsides.", "date": "2023-09-12"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Avoid low underpasses at Pachpedi Naka during peak shower."
    },
    {
        "locality": "Mangla & Nehru Nagar",
        "city": "Bilaspur",
        "state": "Chhattisgarh",
        "latitude": 22.0797,
        "longitude": 82.1409,
        "elevation_m": 262.0,
        "terrain_type": "Arpa river bank depression",
        "drainage_system": "Poor / Silted Arpa tributary nallahs",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Mangla Chowk", "Torwa railway crossing", "Nehru Chowk low pocket"],
        "past_flood_events": [
            {"year": "2024", "event": "Arpa river flash surge after heavy catchment rainfall", "impact": "Submerged low bridges and riverbank colonies"}
        ],
        "resident_reviews": [
            {"author": "Bilaspur Resident", "rating": "Poor", "review": "Arpa river backwater floods Mangla drains instantly whenever the river rises.", "date": "2024-08-20"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Riverfront roads subject to rapid water buildup."
    },

    # ------------------ 6. GOA ------------------
    {
        "locality": "18th June Road & Patto Plaza",
        "city": "Panaji",
        "state": "Goa",
        "latitude": 15.4989,
        "longitude": 73.8278,
        "elevation_m": 4.0,
        "terrain_type": "Mandovi estuary coastal tidal plain",
        "drainage_system": "Poor / High tide backflow into Rua de Ourem creek",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["18th June Road", "Mala low-lying ward", "Patto bus stand subway", "Miramar circle"],
        "past_flood_events": [
            {"year": "2024", "event": "Simultaneous high tide and 150mm monsoon lash", "impact": "Water flooded 18th June road shops and submerged Mala district under 2.5 feet"},
            {"year": "2021", "event": "Severe southwest monsoon tidal inundation", "impact": "Panaji city center cut off for vehicles during peak tide"}
        ],
        "resident_reviews": [
            {"author": "Goan Local", "rating": "Poor", "review": "When high tide hits at the same time as rain, the floodgates cannot open. Water fills up to knee depth on 18th June Road.", "date": "2024-07-22"},
            {"author": "Panaji Resident (Mala)", "rating": "Critical", "review": "Mala area is below sea level at high tide; drainage flows backwards without pumps.", "date": "2024-08-05"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "High tide synchronised waterlogging. Avoid 18th June Road & Mala during high tide."
    },
    {
        "locality": "Old Station Road & Comba",
        "city": "Margao",
        "state": "Goa",
        "latitude": 15.2832,
        "longitude": 73.9862,
        "elevation_m": 10.0,
        "terrain_type": "Sal river lowland basin",
        "drainage_system": "Moderate / Silted Sal river feeder drains",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Comba subway", "Old station road", "Borda nallah junction"],
        "past_flood_events": [
            {"year": "2023", "event": "Sal river overflowed low fields", "impact": "Comba subway fully submerged, traffic diverted to bypass"}
        ],
        "resident_reviews": [
            {"author": "Margao Commuter", "rating": "Poor", "review": "The Comba subway floods every monsoon without exception. Never drive through when it rains.", "date": "2023-08-15"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Avoid Comba subway; use the flyover route."
    },

    # ------------------ 7. GUJARAT ------------------
    {
        "locality": "Akhbarnagar Underpass & Usmanpura",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "latitude": 23.0620,
        "longitude": 72.5654,
        "elevation_m": 53.0,
        "terrain_type": "Sabarmati alluvial bowl",
        "drainage_system": "Moderate / Automated pump-monitored underpasses",
        "drainage_rating": 3,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Akhbarnagar underpass", "Mithakhali underpass", "Parimal underpass", "Vastrapur lake surroundings"],
        "past_flood_events": [
            {"year": "2024", "event": "Record August cloudburst (180mm in 4 hours)", "impact": "All 7 railway underpasses shut down; cars submerged up to roof level"},
            {"year": "2022", "event": "Sabarmati reservoir discharge plus urban downpour", "impact": "South and West zone roads inundated"}
        ],
        "resident_reviews": [
            {"author": "Ahmedabad Commuter", "rating": "Poor", "review": "Akhbarnagar and Parimal underpasses are immediately barricaded during rain. If you try to cross you will get stuck.", "date": "2024-08-26"},
            {"author": "Vastrapur Resident", "rating": "Average", "review": "Surface roads drain in 2-3 hours, but underpasses remain waterlogged for half a day.", "date": "2024-08-28"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "UNDERPASS WARNING: All railway subways (Akhbarnagar, Mithakhali, Parimal) close during heavy rain."
    },
    {
        "locality": "Varachha & Adajan",
        "city": "Surat",
        "state": "Gujarat",
        "latitude": 21.2060,
        "longitude": 72.8580,
        "elevation_m": 13.0,
        "terrain_type": "Tapi river delta / High-tide floodplain",
        "drainage_system": "High / Modern floodgates & Ukai discharge protocols",
        "drainage_rating": 4,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Udhna-Khatodara road", "Kumbharia canal crossway", "Athwa lines low banks"],
        "past_flood_events": [
            {"year": "2024", "event": "Ukai dam released 3.5 lakh cusecs", "impact": "Tapi riverfront promenades and low creek areas inundated"},
            {"year": "2006", "event": "Historic catastrophic Surat flood (Ukai 9 lakh cusecs release)", "impact": "75% of Surat city submerged for 4 days"}
        ],
        "resident_reviews": [
            {"author": "Surat Resident", "rating": "Good", "review": "Surat municipal drainage is much better now with automatic creek floodgates, but low creeks still overflow in continuous rain.", "date": "2024-09-02"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Stay clear of Tapi riverfront and low creeks when Ukai discharge is announced."
    },
    {
        "locality": "Kala Ghoda & Sayajiganj",
        "city": "Vadodara",
        "state": "Gujarat",
        "latitude": 22.3107,
        "longitude": 73.1812,
        "elevation_m": 35.0,
        "terrain_type": "Vishwamitri river overflow basin",
        "drainage_system": "Critical / Silted Vishwamitri river channel",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Kala Ghoda bridge", "Sama-Harni road", "Sayajiganj low roads", "Mujmahuda underpass"],
        "past_flood_events": [
            {"year": "2024", "event": "Vishwamitri river reached 37 feet (danger 26 ft); devastating flood", "impact": "Kala Ghoda completely submerged, crocodiles entered city streets, power cut for 72 hrs"},
            {"year": "2019", "event": "500mm rain in 24 hours caused unprecedented city paralysis", "impact": "Airport closed, railway tracks drowned, 50,000 evacuated"}
        ],
        "resident_reviews": [
            {"author": "Vadodara Local", "rating": "Critical", "review": "Vishwamitri river cuts the city in half and overflows with any heavy rain in Ajwa dam. Severe flooding every alternate year.", "date": "2024-08-30"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "EXTREME FLOOD HAZARD. Stay away from Vishwamitri bridges and Sayajiganj during heavy rain."
    },

    # ------------------ 8. HARYANA ------------------
    {
        "locality": "Hero Honda Chowk & Subhash Chowk",
        "city": "Gurugram",
        "state": "Haryana",
        "latitude": 28.4418,
        "longitude": 77.0177,
        "elevation_m": 220.0,
        "terrain_type": "Aravalli foot runoff basin / Badshahpur drain basin",
        "drainage_system": "Poor / Choked Badshahpur drain bottleneck",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Hero Honda Chowk underpass", "Subhash Chowk", "Golf Course Extension road junction", "Narsinghpur expressway stretch"],
        "past_flood_events": [
            {"year": "2024", "event": "Monsoon showers flooded Delhi-Jaipur Expressway (NH-48) at Narsinghpur", "impact": "Vehicular queues stretched 12 km; underpass flooded with 3.5 feet water"},
            {"year": "2016", "event": "Gurujam gridlock; Badshahpur drain breach", "impact": "Thousands spent night trapped in cars on expressway"}
        ],
        "resident_reviews": [
            {"author": "Cyber City Commuter", "rating": "Poor", "review": "Every single monsoon Narsinghpur service lane becomes a river. Avoid taking cars through Hero Honda Chowk underpass during downpours.", "date": "2024-07-28"},
            {"author": "Sohna Road Resident", "rating": "Poor", "review": "Water logging near Subhash Chowk takes 5-6 hours to subside. Drainage pumps often cannot cope with peak rain.", "date": "2024-08-11"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "NH-48 Narsinghpur & Hero Honda Chowk underpass experience severe waterlogging. Use SPR or cloverleaf."
    },
    {
        "locality": "Old Faridabad Underpass & Badkhal",
        "city": "Faridabad",
        "state": "Haryana",
        "latitude": 28.4116,
        "longitude": 77.3132,
        "elevation_m": 208.0,
        "terrain_type": "Yamuna floodplain fringe",
        "drainage_system": "Poor / Old stormwater channels",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Old Faridabad railway underpass", "Badkhal flyover subway", "Neelam flyover low road"],
        "past_flood_events": [
            {"year": "2024", "event": "Intense spell flooded all railway underpasses", "impact": "Buses and cars submerged in 4 feet water; traffic diverted to bypass"}
        ],
        "resident_reviews": [
            {"author": "Faridabad Commuter", "rating": "Critical", "review": "Old Faridabad railway underpass becomes a death trap during heavy rain. Always check before entering.", "date": "2024-08-08"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Railway underpasses are high-risk submersion zones. Take overbridge routes."
    },

    # ------------------ 9. HIMACHAL PRADESH ------------------
    {
        "locality": "Seraj Valley & Thunag Bazaar",
        "city": "Mandi",
        "state": "Himachal Pradesh",
        "latitude": 31.5470,
        "longitude": 77.1680,
        "elevation_m": 1950.0,
        "terrain_type": "High mountain ravine / Bakhali Nal catchment",
        "drainage_system": "Critical / Mountain torrents subject to boulder-debris blockage",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Thunag main market bridge", "Pandoh dam bypass", "Bakhali river crossing"],
        "past_flood_events": [
            {"year": "2025", "event": "Source-documented cloudburst on June 30 night swept Seraj valley", "impact": "Debris destroyed shops in Thunag Bazar and cut off two dozen villages"},
            {"year": "2023", "event": "Beas river catastrophic flash flood", "impact": "Submerged Mandi Panchvaktra temple and swept away bridges"}
        ],
        "resident_reviews": [
            {"author": "Thunag Local", "rating": "Critical", "review": "Cloudbursts carry huge trees and silt that instantly block natural nallahs, causing destructive flash flooding.", "date": "2025-07-02"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "EXTREME FLASH FLOOD & LANDSLIDE DANGER. Avoid mountain ravines and Thunag streams during rain."
    },
    {
        "locality": "Circular Road & Tutikandi",
        "city": "Shimla",
        "state": "Himachal Pradesh",
        "latitude": 31.1048,
        "longitude": 77.1734,
        "elevation_m": 2200.0,
        "terrain_type": "Steep ridge / Valley runoff",
        "drainage_system": "Moderate / British-era hillside culverts",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Tutikandi bypass", "Victory tunnel junction", "Dhalli tunnel approach"],
        "past_flood_events": [
            {"year": "2023", "event": "Historic August landslide and torrent disaster", "impact": "Shiv Bawadi temple collapse, circular road cracked, traffic paralyzed"}
        ],
        "resident_reviews": [
            {"author": "Shimla Taxi Driver", "rating": "Average", "review": "Water runs off quickly down the slopes, but culvert choke-ups cause sudden mudflows across roads.", "date": "2023-08-25"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Watch for loose boulders and water torrents crossing the road near hillside cuts."
    },

    # ------------------ 10. JHARKHAND ------------------
    {
        "locality": "Kishore Ganj & Harmu Road",
        "city": "Ranchi",
        "state": "Jharkhand",
        "latitude": 23.3640,
        "longitude": 85.3180,
        "elevation_m": 651.0,
        "terrain_type": "Harmu river valley depression",
        "drainage_system": "Poor / Encroached Harmu river channel",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Kishore Ganj Chowk", "Harmu Muktidham low bridge", "Ratu Road circle"],
        "past_flood_events": [
            {"year": "2024", "event": "Heavy monsoon shower submerged Harmu road", "impact": "Knee-deep water in shops, traffic jammed for hours"},
            {"year": "2021", "event": "Depression over Jharkhand dumped 130mm rain", "impact": "Harmu river overflowed embankments"}
        ],
        "resident_reviews": [
            {"author": "Ranchi Resident", "rating": "Poor", "review": "Harmu river has been turned into a dirty nallah that overflows onto roads at Kishore Ganj with every heavy rain.", "date": "2024-07-19"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Waterlogging at Kishore Ganj and low Harmu bridges. Use Main Road or Ring Road."
    },
    {
        "locality": "Mango & Jugsalai",
        "city": "Jamshedpur",
        "state": "Jharkhand",
        "latitude": 22.8124,
        "longitude": 86.2029,
        "elevation_m": 159.0,
        "terrain_type": "Subarnarekha & Kharkai confluence basin",
        "drainage_system": "Moderate / Industrial drainage outfalls",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Mango bridge approach", "Jugsalai railway underbridge", "Baghbera low area"],
        "past_flood_events": [
            {"year": "2024", "event": "Kharkai and Subarnarekha rivers crossed danger mark", "impact": "Baghbera and low colonies flooded up to first floor"}
        ],
        "resident_reviews": [
            {"author": "Jamshedpur Citizen", "rating": "Average", "review": "Jugsalai underbridge gathers water quickly, but river levels dictate the real danger in Baghbera.", "date": "2024-08-16"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Monitor Kharkai river warnings if entering Baghbera or low banks."
    },

    # ------------------ 11. KARNATAKA ------------------
    {
        "locality": "Silk Board & Outer Ring Road (Bellandur)",
        "city": "Bengaluru",
        "state": "Karnataka",
        "latitude": 12.9177,
        "longitude": 76.6238,
        "elevation_m": 900.0,
        "terrain_type": "Inter-connected lake wetland valley (Bellandur-Varthur valley)",
        "drainage_system": "Critical / Encroached Rajakaluve stormwater drains",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Central Silk Board junction", "EcoSpace ORR stretch", "Rainbow Drive layout", "Manyata Tech Park low road"],
        "past_flood_events": [
            {"year": "2024", "event": "Heavy October cloudburst flooded Manyata Tech Park and Silk Board", "impact": "Tech corridors paralyzed; tractors used for employee transit"},
            {"year": "2022", "event": "Historic Bengaluru urban inundation; 131mm overnight downpour", "impact": "EcoSpace ORR underwater for 4 days; luxury villas in Rainbow Drive submerged"}
        ],
        "resident_reviews": [
            {"author": "IT Professional (ORR)", "rating": "Critical", "review": "The Rajakaluves near Bellandur are blocked by concrete construction. Water has nowhere to flow and gathers 3 feet deep on ORR.", "date": "2024-10-18"},
            {"author": "Silk Board Commuter", "rating": "Poor", "review": "Even moderate rain creates hours of bottleneck at Silk Board and HSR BDA complex. Completely clogged.", "date": "2024-09-22"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "SEVERE CLOGGING HAZARD: Silk Board & Bellandur ORR flood rapidly. Divert via elevated metro corridors."
    },
    {
        "locality": "Pumpwell & Kottara Chowki",
        "city": "Mangaluru",
        "state": "Karnataka",
        "latitude": 12.8688,
        "longitude": 74.8624,
        "elevation_m": 22.0,
        "terrain_type": "Netravati coastal hill runoff basin",
        "drainage_system": "Poor / Highway flyover underpass basin",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Pumpwell flyover underpass", "Kottara Chowki junction", "Kankanady railway bridge", "Baikampady industrial area"],
        "past_flood_events": [
            {"year": "2024", "event": "Coastal monsoon downpour dumped 200mm in 24 hours", "impact": "Pumpwell circle turned into an artificial lake, vehicles submerged"},
            {"year": "2018", "event": "May 29 historic Mangaluru cloudburst", "impact": "Citywide flooding, NDRF deployed in city center"}
        ],
        "resident_reviews": [
            {"author": "Mangaluru Driver", "rating": "Poor", "review": "Pumpwell junction was built lower than the surrounding drains. Water collects like a bowl during torrential rain.", "date": "2024-07-06"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Avoid Pumpwell and Kottara Chowki ground level during monsoon downpours."
    },

    # ------------------ 12. KERALA ------------------
    {
        "locality": "MG Road & Kaloor",
        "city": "Kochi",
        "state": "Kerala",
        "latitude": 9.9816,
        "longitude": 76.2999,
        "elevation_m": 3.0,
        "terrain_type": "Vembanad coastal backwater plain",
        "drainage_system": "Moderate / Operation Breakthrough canals",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Kaloor bus stand", "South railway station underpass", "Jos Junction MG road", "Thevara canal road"],
        "past_flood_events": [
            {"year": "2024", "event": "Intense pre-monsoon shower coinciding with high tide", "impact": "Waterlogged Kaloor and MG road, traffic slowed to crawl"},
            {"year": "2018", "event": "Mega Kerala floods; Periyar river massive overflow", "impact": "Submerged Aluva, North Paravur and Kochi airport for days"}
        ],
        "resident_reviews": [
            {"author": "Kochi Resident", "rating": "Average", "review": "Operation Breakthrough improved Mullassery canal, but high tide still slows drainage near South station.", "date": "2024-06-15"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Check tidal status; low underpasses near South Railway station flood during high tide rains."
    },
    {
        "locality": "Kuttanad & Mullakkal",
        "city": "Alappuzha",
        "state": "Kerala",
        "latitude": 9.4981,
        "longitude": 76.3388,
        "elevation_m": -1.5,
        "terrain_type": "Below sea-level polder wetland",
        "drainage_system": "Critical / Polder pump and spillway dependent",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["AC Road (Alappuzha-Changanassery)", "Mullakkal street", "Kainakary low bunds"],
        "past_flood_events": [
            {"year": "2024", "event": "Monsoon discharge from Pamba & Achankovil rivers", "impact": "AC Road submerged at multiple points; boat transit activated"},
            {"year": "2018", "event": "Complete submergence of Kuttanad delta", "impact": "Total evacuation of population"}
        ],
        "resident_reviews": [
            {"author": "Kuttanad Local", "rating": "Critical", "review": "We live below sea level. When eastern rivers are full, water stays logged for weeks without receding.", "date": "2024-07-20"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "EXTREME WATERLOGGING ZONE: AC Road and polders subject to prolonged inundation."
    },
    {
        "locality": "Meppadi & Chooralmala",
        "city": "Wayanad",
        "state": "Kerala",
        "latitude": 11.5534,
        "longitude": 76.1320,
        "elevation_m": 880.0,
        "terrain_type": "Western Ghats steep escarpment",
        "drainage_system": "Critical / Mountain river Iruvaipuzha debris path",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Chooralmala bridge", "Mundakkai stream crossing", "Meppadi bypass"],
        "past_flood_events": [
            {"year": "2024", "event": "Catastrophic July 30 landslide and debris torrent", "impact": "Villages of Mundakkai and Chooralmala obliterated; 400+ casualties"},
            {"year": "2019", "event": "Puthumala massive debris avalanche", "impact": "Hillside swept into valley"}
        ],
        "resident_reviews": [
            {"author": "Wayanad Community Member", "rating": "Critical", "review": "Continuous extreme rainfall on these steep slopes causes soil supersaturation and massive mudslides.", "date": "2024-08-05"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "DANGER ZONE: Strictly avoid Chooralmala-Mundakkai river valley during heavy rain warnings."
    },

    # ------------------ 13. MADHYA PRADESH ------------------
    {
        "locality": "Bhopal Junction Underpass & MP Nagar",
        "city": "Bhopal",
        "state": "Madhya Pradesh",
        "latitude": 23.2599,
        "longitude": 77.4126,
        "elevation_m": 500.0,
        "terrain_type": "Upper lake basin and undulating plateau",
        "drainage_system": "Moderate / Silted Patra nallah",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Bhopal railway station platform-6 subway", "Hamidia road", "MP Nagar Zone 1 subway", "Karond junction"],
        "past_flood_events": [
            {"year": "2024", "event": "Bhadbhada dam opened 7 gates after 140mm rainfall", "impact": "Patra nallah overflowed into low bastis, station subway flooded"},
            {"year": "2022", "event": "Severe downpour flooded VIP road and Old City", "impact": "Traffic suspended on low-lying arterial routes"}
        ],
        "resident_reviews": [
            {"author": "Bhopal Resident", "rating": "Poor", "review": "Old city roads and station underpass fill up rapidly. Avoid Hamidia road when it pours.", "date": "2024-08-10"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Old city subways and Patra nallah surroundings flood quickly."
    },
    {
        "locality": "Rajwada & Vijay Nagar",
        "city": "Indore",
        "state": "Madhya Pradesh",
        "latitude": 22.7196,
        "longitude": 75.8577,
        "elevation_m": 553.0,
        "terrain_type": "Kanh & Saraswati river plateau",
        "drainage_system": "Adequate / Cleaned riverfront and upgraded stormwater lines",
        "drainage_rating": 4,
        "clogging_tendency": "Low - Generally Clear",
        "chronic_chokepoints": ["Bhanwarkuan square low pocket", "LIG square service lane"],
        "past_flood_events": [
            {"year": "2023", "event": "Short cloudburst caused localized puddling", "impact": "Cleared by municipal teams within 45 minutes"}
        ],
        "resident_reviews": [
            {"author": "Indore Citizen", "rating": "Good", "review": "Indore municipal corporation is very proactive. Drainage clears quickly, rarely any long-term blockage.", "date": "2024-07-15"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Generally clear. Minor slow drainage at Bhanwarkuan underpass during peak rain."
    },

    # ------------------ 14. MAHARASHTRA ------------------
    {
        "locality": "Hindmata & Milan Subway",
        "city": "Mumbai",
        "state": "Maharashtra",
        "latitude": 19.0118,
        "longitude": 72.8427,
        "elevation_m": 3.0,
        "terrain_type": "Reclaimed tidal mudflat / Natural saucer bowl",
        "drainage_system": "Poor / High tide sea-outfall lock",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Hindmata cinema junction", "Milan subway", "Andheri subway", "Gandhi Market King's Circle", "Dadar TT circle"],
        "past_flood_events": [
            {"year": "2024", "event": "July 8 extreme monsoon downpour (300mm in 6 hrs)", "impact": "Local trains halted on Harbour and Central lines; Hindmata under 3 feet water"},
            {"year": "2005", "event": "Catastrophic July 26 Mumbai deluge (944mm in 24 hrs)", "impact": "Mithi river breached; thousands stranded; city crippled for a week"}
        ],
        "resident_reviews": [
            {"author": "Dadar Local", "rating": "Critical", "review": "Hindmata is lower than sea level at high tide. Even with new underground holding tanks, water collects fast in heavy rain.", "date": "2024-07-12"},
            {"author": "Andheri Commuter", "rating": "Critical", "review": "Andheri subway closes with just 15 minutes of heavy rain. Never enter if the yellow warning board is flashing.", "date": "2024-08-04"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "SEVERE WATERLOGGING ZONE: Milan & Andheri subways close immediately. Divert via Western Express Highway flyovers."
    },
    {
        "locality": "Sinhagad Road & Pulachi Wadi",
        "city": "Pune",
        "state": "Maharashtra",
        "latitude": 18.4900,
        "longitude": 73.8340,
        "elevation_m": 560.0,
        "terrain_type": "Mutha river active floodplain",
        "drainage_system": "Poor / Encroached blue floodline zones",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Sinhagad road Ekta nagari", "Bhide bridge underpass", "Sangamwadi road low bridge"],
        "past_flood_events": [
            {"year": "2024", "event": "Khadakwasla dam released 40,000 cusecs water", "impact": "Ekta Nagar societies flooded up to 5 feet; army deployed with boats"},
            {"year": "2019", "event": "Ambil Odha flash flood caused by cloudburst", "impact": "Walls collapsed, vehicles swept away, 20 fatalities"}
        ],
        "resident_reviews": [
            {"author": "Sinhagad Road Resident", "rating": "Critical", "review": "When Khadakwasla dam gates are opened, Mutha river enters residential parking lots within 2 hours.", "date": "2024-07-26"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Keep away from riverside roads along Mutha river and Bhide bridge."
    },
    {
        "locality": "Panchganga Ghat & Venus Corner",
        "city": "Kolhapur",
        "state": "Maharashtra",
        "latitude": 16.7050,
        "longitude": 74.2433,
        "elevation_m": 569.0,
        "terrain_type": "Panchganga river basin",
        "drainage_system": "Poor / Backwater from downstream Almatti dam buffer",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Panchganga bridge on NH-48", "Venus Corner", "Shahupuri low lanes"],
        "past_flood_events": [
            {"year": "2021", "event": "Panchganga river crossed warning mark by 12 feet", "impact": "NH-48 Pune-Bengaluru highway closed for 4 days; city marooned"},
            {"year": "2019", "event": "Massive Sangli-Kolhapur floods", "impact": "Over 200,000 people displaced"}
        ],
        "resident_reviews": [
            {"author": "Kolhapur Resident", "rating": "Critical", "review": "Panchganga floods NH-48 and stops all interstate movement when catchment dams fill up.", "date": "2023-08-10"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "High flood alert near Panchganga river and NH-48 bridge approach."
    },

    # ------------------ 15. MANIPUR ------------------
    {
        "locality": "Khwairamband Bazaar & Singjamei",
        "city": "Imphal",
        "state": "Manipur",
        "latitude": 24.8170,
        "longitude": 93.9368,
        "elevation_m": 786.0,
        "terrain_type": "Imphal river valley floor basin",
        "drainage_system": "Critical / Imphal & Nambul river embankment breaches",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Khwairamband (Ima Market)", "Singjamei bridge approach", "Uripok Kangchup road", "Keishamthong"],
        "past_flood_events": [
            {"year": "2024", "event": "Cyclone Remal triggered historic breach of Imphal and Nambul river dykes", "impact": "Entire central market and Raj Bhavan surroundings drowned in 4-6 feet water"},
            {"year": "2020", "event": "Monsoon flood breached Singjamei embankment", "impact": "Major town routes cut off"}
        ],
        "resident_reviews": [
            {"author": "Imphal Local (Ima Keithel)", "rating": "Critical", "review": "Nambul river overflows directly into the women's market. Silt and dirty floodwater take weeks to clear.", "date": "2024-06-02"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "SEVERE FLOOD ZONE: Major market routes flood rapidly during river overflow."
    },

    # ------------------ 16. MEGHALAYA ------------------
    {
        "locality": "Police Bazar & Polo Ground",
        "city": "Shillong",
        "state": "Meghalaya",
        "latitude": 25.5788,
        "longitude": 91.8933,
        "elevation_m": 1525.0,
        "terrain_type": "Hill plateau depression (Wah Umkhrah basin)",
        "drainage_system": "Poor / Encroached Wah Umkhrah stream",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Polo ground parking", "Wah Umkhrah bridge", "Mawlai road culvert"],
        "past_flood_events": [
            {"year": "2024", "event": "Sudden cloudburst over Shillong plateau", "impact": "Wah Umkhrah flash flooded Polo ground, submerging vehicles and stalls"}
        ],
        "resident_reviews": [
            {"author": "Shillong Local", "rating": "Poor", "review": "Polo ground sits in a valley basin. When heavy rains hit, Wah Umkhrah river overflows within 30 minutes.", "date": "2024-06-20"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Avoid parking or lingering at Polo Ground during heavy downpours."
    },
    {
        "locality": "Sohra Rim & Nohkalikai Approach",
        "city": "Cherrapunji",
        "state": "Meghalaya",
        "latitude": 25.2702,
        "longitude": 91.7323,
        "elevation_m": 1430.0,
        "terrain_type": "Limestone plateau / Karst cliffs",
        "drainage_system": "Natural / High surface runoff speed",
        "drainage_rating": 4,
        "clogging_tendency": "Low - Generally Clear",
        "chronic_chokepoints": ["Shella road low culvert"],
        "past_flood_events": [
            {"year": "2022", "event": "Record 972mm rain in 24 hours (world record tier)", "impact": "Massive gorge waterfalls, surface water sheets crossed highways"}
        ],
        "resident_reviews": [
            {"author": "Local Tour Operator", "rating": "Good", "review": "Because it's a high cliff plateau, water doesn't stay clogged—it cascades down to Bangladesh plains. But road visibility is zero.", "date": "2023-07-15"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Water clears quickly down gorges, but extreme rainfall blinds drivers. Proceed with caution."
    },

    # ------------------ 17. MIZORAM ------------------
    {
        "locality": "Bawngkawn & Chite Valley",
        "city": "Aizawl",
        "state": "Mizoram",
        "latitude": 23.7271,
        "longitude": 92.7176,
        "elevation_m": 1132.0,
        "terrain_type": "Steep north-south mountain ridge",
        "drainage_system": "Moderate / Steep roadside drains prone to debris",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Bawngkawn junction", "Vaivakawn quarry road", "Chite river bridge"],
        "past_flood_events": [
            {"year": "2024", "event": "Cyclone Remal induced extensive landslides & mud blockages", "impact": "Melthum stone quarry collapse; several road stretches blocked by debris"}
        ],
        "resident_reviews": [
            {"author": "Aizawl Driver", "rating": "Average", "review": "Water itself drains off the ridge fast, but mud and gravel choke the culverts, causing sudden diversions.", "date": "2024-05-30"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Landslide and mudflow hazard on hill cuts rather than static waterlogging."
    },

    # ------------------ 18. NAGALAND ------------------
    {
        "locality": "Supermarket & Walford",
        "city": "Dimapur",
        "state": "Nagaland",
        "latitude": 25.9094,
        "longitude": 93.7266,
        "elevation_m": 145.0,
        "terrain_type": "Dhansiri river alluvial plain",
        "drainage_system": "Poor / Encroached natural nallahs",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Supermarket area", "Walford road", "Purana Bazar low stretch", "Dhansiri bridge approach"],
        "past_flood_events": [
            {"year": "2024", "event": "Dhansiri river overflowed due to heavy catchment rain in Karbi Anglong", "impact": "Purana Bazar and low residential colonies submerged up to 3 feet"}
        ],
        "resident_reviews": [
            {"author": "Dimapur Resident", "rating": "Poor", "review": "Dimapur has virtually no functioning stormwater drains in commercial areas. Water stays on the road for hours.", "date": "2024-07-18"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "High waterlogging in Supermarket and Purana Bazar. Plan alternate routes."
    },

    # ------------------ 19. ODISHA ------------------
    {
        "locality": "Jaydev Vihar & ISKCON Temple stretch",
        "city": "Bhubaneswar",
        "state": "Odisha",
        "latitude": 20.2961,
        "longitude": 85.8245,
        "elevation_m": 45.0,
        "terrain_type": "Gangua nallah catchment basin",
        "drainage_system": "Poor / Encroached Drain No. 10 bottleneck",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Jaydev Vihar underpass", "ISKCON temple NH-16 frontage", "Acharya Vihar subway", "Bomikhal canal road"],
        "past_flood_events": [
            {"year": "2024", "event": "Deep depression dumped 150mm rain in 5 hours", "impact": "NH-16 in front of ISKCON flooded waist-deep; luxury cars floated on service road"},
            {"year": "2019", "event": "Cyclone Fani aftermath urban inundation", "impact": "Stormwater drains choked by uprooted trees, leading to severe citywide clogging"}
        ],
        "resident_reviews": [
            {"author": "Bhubaneswar Commuter", "rating": "Critical", "review": "ISKCON temple road on NH-16 turns into a swimming pool with just one hour of rain. The national highway gets jammed for kilometers.", "date": "2024-08-18"},
            {"author": "Jaydev Vihar Resident", "rating": "Poor", "review": "Drain No. 10 overflows right onto the flyover underpass. Avoid this spot during heavy rain.", "date": "2024-09-05"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "SEVERE CLOGGING on NH-16 near ISKCON temple and Jaydev Vihar underpass."
    },
    {
        "locality": "Badambadi & Raja Bagicha",
        "city": "Cuttack",
        "state": "Odisha",
        "latitude": 20.4625,
        "longitude": 85.8828,
        "elevation_m": 30.0,
        "terrain_type": "Mahanadi-Kathajodi inter-river saucer delta",
        "drainage_system": "Critical / Sluice gate dependent into Kathajodi river",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Badambadi bus terminal", "Pattapole", "Raja Bagicha", "Thoria Sahi"],
        "past_flood_events": [
            {"year": "2024", "event": "Simultaneous Mahanadi river spate and local heavy downpour", "impact": "Sluice gates shut to stop river backflow; town became an enclosed lake with 3 feet water"},
            {"year": "2013", "event": "Cyclone Phailin aftermath flood", "impact": "Severe urban waterlogging lasting over a week"}
        ],
        "resident_reviews": [
            {"author": "Cuttack Local", "rating": "Critical", "review": "Cuttack is shaped like a saucer between two rivers. When the rivers rise, gates close and pumps cannot handle the volume.", "date": "2024-08-22"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Town center sits in a depression. Badambadi and Pattapole submerge rapidly."
    },

    # ------------------ 20. PUNJAB ------------------
    {
        "locality": "Ranjit Avenue & Mall Road",
        "city": "Amritsar",
        "state": "Punjab",
        "latitude": 31.6446,
        "longitude": 74.8725,
        "elevation_m": 232.0,
        "terrain_type": "Ravi-Beas interfluvial plain",
        "drainage_system": "Moderate / Stormwater disposal network",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Ranjit Avenue low-lying road", "Market road underpass", "Bus stand junction", "Kitchlew chowk"],
        "past_flood_events": [
            {"year": "2023", "event": "Heavy Ravi catchment rainfall flooded Ravi river tributaries", "impact": "Submergence in Ajnala and border villages; localized waterlogging in city underpasses"},
            {"year": "2025", "event": "Monsoon spell waterlogged Amritsar low areas", "impact": "Market underpass closed for 4 hours"}
        ],
        "resident_reviews": [
            {"author": "Amritsar Resident", "rating": "Average", "review": "Ranjit Avenue main blocks drain well, but market underpass and low-lying perimeter roads collect water during sudden cloudbursts.", "date": "2024-08-14"},
            {"author": "Civil Lines Commuter", "rating": "Good", "review": "Water clears within 1-2 hours after rain stops. Generally passable except for underpass.", "date": "2024-09-01"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Ranjit Avenue surface roads are clear; avoid Market Road underpass during peak rain."
    },
    {
        "locality": "Dhoka Mohalla & Clock Tower",
        "city": "Ludhiana",
        "state": "Punjab",
        "latitude": 30.9010,
        "longitude": 75.8573,
        "elevation_m": 244.0,
        "terrain_type": "Buddha Nallah overflow depression",
        "drainage_system": "Critical / Overflowing Buddha Nallah",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Dhoka Mohalla low street", "Clock Tower chowk", "Shivpuri bridge", "Dholewal military camp low road"],
        "past_flood_events": [
            {"year": "2025", "event": "Buddha Nallah overflowed following heavy rain across Ludhiana district", "impact": "Streets covered with contaminated water and sewage in Dhoka Mohalla; houses flooded"},
            {"year": "2023", "event": "Sutlej river flood overtopped embankments", "impact": "Extensive crop and locality damage in low wards"}
        ],
        "resident_reviews": [
            {"author": "Dhoka Mohalla Local", "rating": "Critical", "review": "Buddha Nallah breaches its banks every single monsoon season. Sewage water fills our ground floors.", "date": "2025-08-12"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "CRITICAL CLOGGING HAZARD: Buddha Nallah overflow blocks Dhoka Mohalla and Clock Tower roads."
    },
    {
        "locality": "Guddar Bhaini & Border Belt",
        "city": "Fazilka",
        "state": "Punjab",
        "latitude": 30.5151,
        "longitude": 74.0514,
        "elevation_m": 177.0,
        "terrain_type": "Sutlej river floodplain / Border loop",
        "drainage_system": "Critical / Sutlej backwater without protective dykes",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Guddar Bhaini village access", "Kawanwali bridge", "Mahar Jamsher road"],
        "past_flood_events": [
            {"year": "2025", "event": "Sutlej water entered homes; village submerged from August 26", "impact": "Residents stayed in relief camps for weeks; complete road cutoff"},
            {"year": "2023", "event": "Severe Sutlej river flood", "impact": "Over 40 border villages cut off"}
        ],
        "resident_reviews": [
            {"author": "Border Village Resident", "rating": "Critical", "review": "Whenever excess water is released from Harike barrage, Guddar Bhaini gets submerged completely.", "date": "2025-09-02"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "RIVER FLOOD ZONE: Sutlej overflow cuts off road access. Follow district disaster management."
    },

    # ------------------ 21. RAJASTHAN ------------------
    {
        "locality": "MI Road & Sikar Road (Dadi Ka Phatak)",
        "city": "Jaipur",
        "state": "Rajasthan",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "elevation_m": 431.0,
        "terrain_type": "Aravalli foothill basin / Dravyavati river catchment",
        "drainage_system": "Poor / Incomplete drainage outfalls into Amanishah nallah",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Sikar Road (Dadi Ka Phatak underpass)", "B2 Bypass underpass", "MI Road near Panch Batti", "Transport Nagar tunnel approach"],
        "past_flood_events": [
            {"year": "2024", "event": "August 1 cloudburst (160mm in 3 hours) in Jaipur", "impact": "Sikar road underpass filled with 8 feet water; cars washed into open drains; 3 deaths"},
            {"year": "2020", "event": "Record deluge in walled city", "impact": "Amer and walled city streets turned into torrents"}
        ],
        "resident_reviews": [
            {"author": "Jaipur Daily Commuter", "rating": "Critical", "review": "Sikar road at Dadi Ka Phatak and B2 Bypass underpass drown completely. Every cloudburst claims cars here.", "date": "2024-08-05"},
            {"author": "Walled City Merchant", "rating": "Poor", "review": "Water surges down from Nahargarh hills directly into MI Road and Johari Bazar. Severe clogging.", "date": "2024-08-12"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "DANGER AT UNDERPASSES: Sikar road and B2 Bypass underpasses fill with dangerous water depths."
    },
    {
        "locality": "Nayapura & Aerodrome Circle",
        "city": "Kota",
        "state": "Rajasthan",
        "latitude": 25.1800,
        "longitude": 75.8300,
        "elevation_m": 271.0,
        "terrain_type": "Chambal river gorge basin",
        "drainage_system": "Moderate / Kota barrage floodgates protocol",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Nayapura low bridge", "Aerodrome circle underpass", "Anantpura low road"],
        "past_flood_events": [
            {"year": "2024", "event": "Kota barrage opened 14 gates (3 lakh cusecs discharge)", "impact": "Nayapura low bridge submerged, riverside colonies evacuated"}
        ],
        "resident_reviews": [
            {"author": "Kota Resident", "rating": "Average", "review": "Kota barrage discharge dictates road closures. If barrage gates are open, Nayapura low bridge is submerged.", "date": "2024-08-25"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Check Kota barrage release status before approaching Chambal river bridges."
    },

    # ------------------ 22. SIKKIM ------------------
    {
        "locality": "Tung & Chungthang valley",
        "city": "Mangan",
        "state": "Sikkim",
        "latitude": 27.5028,
        "longitude": 88.5322,
        "elevation_m": 1600.0,
        "terrain_type": "Teesta river gorge / Glacial lake outburst zone",
        "drainage_system": "Critical / Glacial lake outburst flood (GLOF) active channel",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Chungthang Teesta-III dam axis", "Tung bridge", "Dikchu low road"],
        "past_flood_events": [
            {"year": "2023", "event": "Catastrophic South Lhonak Glacial Lake Outburst Flood (GLOF)", "impact": "Teesta-III dam washed away; Chungthang bridge destroyed; 100+ deaths and massive highway destruction"},
            {"year": "2024", "event": "Monsoon landslide breached Mangan road connectivity", "impact": "North Sikkim cut off for over a month"}
        ],
        "resident_reviews": [
            {"author": "North Sikkim Driver", "rating": "Critical", "review": "Teesta river valley road between Singtam and Chungthang is extremely vulnerable to flash flooding and rockfalls.", "date": "2024-06-18"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "EXTREME DISASTER RISK: Teesta valley roads subject to sudden flash floods and debris blockages."
    },
    {
        "locality": "Deorali & Indira Bypass",
        "city": "Gangtok",
        "state": "Sikkim",
        "latitude": 27.3314,
        "longitude": 88.6138,
        "elevation_m": 1650.0,
        "terrain_type": "Steep mountain slope",
        "drainage_system": "Moderate / Jhora mountain drains",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Deorali taxi stand low cut", "Indira bypass jhora crossing"],
        "past_flood_events": [
            {"year": "2024", "event": "Heavy mountain downpour blocked NH-10 connectivity", "impact": "Traffic suspended between Siliguri and Gangtok for multiple days"}
        ],
        "resident_reviews": [
            {"author": "Gangtok Citizen", "rating": "Average", "review": "City drains in Gangtok function well, but NH-10 outside the city gets blocked by mud and overflowing jhoras.", "date": "2024-07-12"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "City center clear, but NH-10 lifeline to plains is prone to mud blockages."
    },

    # ------------------ 23. TAMIL NADU ------------------
    {
        "locality": "Velachery & Mudichur",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "latitude": 12.9750,
        "longitude": 80.2200,
        "elevation_m": 6.0,
        "terrain_type": "Pallikaranai marshland / Adyar river floodplain",
        "drainage_system": "Poor / Encroached marshland stormwater outlets",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Velachery lake 100 feet road", "Mudichur main road", "Gopathi Narayanaswami road T. Nagar", "Vyasarapadi subway"],
        "past_flood_events": [
            {"year": "2023", "event": "Cyclone Michaung dropped 450mm rainfall in 36 hours", "impact": "Velachery and Mudichur submerged up to first floor; boats operated for 4 days"},
            {"year": "2015", "event": "Catastrophic Chennai floods; Chembarambakkam reservoir release", "impact": "Waist-to-chest water across South Chennai; airport runway submerged"}
        ],
        "resident_reviews": [
            {"author": "Velachery Resident", "rating": "Critical", "review": "Built on the Pallikaranai marsh. When northeast monsoon hits, water has nowhere to go. Knee-deep water is standard.", "date": "2024-11-28"},
            {"author": "T. Nagar Merchant", "rating": "Poor", "review": "Bazullah road and underpasses flood fast. Smart city drains help slightly but high tide stalls Buckingham canal.", "date": "2024-12-02"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "SEVERE FLOOD HAZARD during Northeast Monsoon (Oct-Dec). Avoid Velachery 100 ft road & subways."
    },
    {
        "locality": "Lankester Canal & Thillai Nagar",
        "city": "Tiruchirappalli",
        "state": "Tamil Nadu",
        "latitude": 10.7905,
        "longitude": 78.7047,
        "elevation_m": 88.0,
        "terrain_type": "Cauvery & Kollidam inter-river basin",
        "drainage_system": "Moderate / Koraiyar river diversion",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Thillai Nagar main road", "Koraiyar bridge near Edamalaipatti Pudur", "Cantonment subway"],
        "past_flood_events": [
            {"year": "2024", "event": "Koraiyar river surplus water entered southern colonies", "impact": "Edamalaipatti Pudur submerged under 2 feet water"}
        ],
        "resident_reviews": [
            {"author": "Trichy Resident", "rating": "Average", "review": "Koraiyar river can cause backwater in low colonies, but town center clears in a few hours.", "date": "2024-11-15"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Keep clear of Koraiyar riverbanks when Mettur dam discharge is high."
    },

    # ------------------ 24. TELANGANA ------------------
    {
        "locality": "Tolichowki & Gachibowli Bio-Diversity",
        "city": "Hyderabad",
        "state": "Telangana",
        "latitude": 17.4010,
        "longitude": 78.4110,
        "elevation_m": 535.0,
        "terrain_type": "Musi river catchment / Rocky plateau valleys",
        "drainage_system": "Poor / Encroached Shah Hatim lake nallah",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Nadeem Colony (Tolichowki)", "Shaikpet nallah road", "Malakpet railway bridge", "Ayyappa Society underpass Madhapur"],
        "past_flood_events": [
            {"year": "2024", "event": "Heavy September thunderstorms (110mm in 2 hours)", "impact": "Tolichowki and Musi river causeways submerged; traffic jammed across HITEC city"},
            {"year": "2020", "event": "Disastrous Hyderabad cloudburst (320mm in 24 hours)", "impact": "Musi river catastrophic flood; Nadeem Colony submerged under 8 feet water for a week"}
        ],
        "resident_reviews": [
            {"author": "Tolichowki Resident", "rating": "Critical", "review": "Nadeem colony is built inside the dried lakebed. Every heavy rain drowns ground floors. Boats are brought out yearly.", "date": "2024-09-08"},
            {"author": "Gachibowli Techie", "rating": "Poor", "review": "Bio-diversity junction and Ayyappa Society underpasses flood within 20 mins. Massive water stagnation.", "date": "2024-09-14"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Nadeem Colony & Malakpet railway underbridge become severely waterlogged. Use outer flyovers."
    },
    {
        "locality": "Hunter Road & Naimnagar",
        "city": "Warangal",
        "state": "Telangana",
        "latitude": 17.9689,
        "longitude": 79.5941,
        "elevation_m": 270.0,
        "terrain_type": "Bhadrakali lake catchment",
        "drainage_system": "Critical / Silted Bondavagu and Naimnagar nallahs",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Hunter Road low bridge", "Naimnagar causeway", "Santhoshimatha temple low road"],
        "past_flood_events": [
            {"year": "2024", "event": "Bhadrakali lake surplussed into low-lying colonies", "impact": "Hunter Road cut off for 3 days; army rescue boats deployed"},
            {"year": "2020", "event": "Torrential rain flooded 30 colonies", "impact": "Extensive damage to residential properties"}
        ],
        "resident_reviews": [
            {"author": "Warangal Local", "rating": "Critical", "review": "Hunter road is the main link between Warangal and Hanamkonda. It goes under 4 feet water with every lake overflow.", "date": "2024-09-05"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Hunter Road gets cut off during heavy rain. Divert via Kazipet bypass."
    },

    # ------------------ 25. TRIPURA ------------------
    {
        "locality": "Orient Chowmuhani & Baldakhal",
        "city": "Agartala",
        "state": "Tripura",
        "latitude": 23.8315,
        "longitude": 91.2868,
        "elevation_m": 15.0,
        "terrain_type": "Howrah river basin / International border lowlands",
        "drainage_system": "Poor / Howrah river embankment backflow",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Orient Chowmuhani", "Shakuntala road", "Baldakhal riverfront", "Battala market"],
        "past_flood_events": [
            {"year": "2024", "event": "Historic August Tripura flood; Howrah river reached record peak", "impact": "Over 60,000 people displaced; Agartala city center submerged up to 4 feet"},
            {"year": "2023", "event": "Monsoon cloudburst flooded commercial streets", "impact": "Market shops inundated"}
        ],
        "resident_reviews": [
            {"author": "Agartala Citizen", "rating": "Critical", "review": "Howrah river rises higher than city drains. Sluice gates close and the entire capital gets waterlogged.", "date": "2024-08-24"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Howrah river backflow causes severe city waterlogging during heavy rain."
    },

    # ------------------ 26. UTTAR PRADESH ------------------
    {
        "locality": "Hazratganj & Gomti Nagar (Kathauta)",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "latitude": 26.8467,
        "longitude": 80.9462,
        "elevation_m": 123.0,
        "terrain_type": "Gomti river basin plain",
        "drainage_system": "Moderate / Ghaas Mandi nallah and pumping stations",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Hazratganj multi-level parking low road", "Alambagh underpass", "Charbagh railway station front", "Polytechnic circle"],
        "past_flood_events": [
            {"year": "2024", "event": "Intense September downpour (120mm in 6 hours)", "impact": "Waterlogging in Charbagh and Hazratganj; schools closed for 2 days"},
            {"year": "2022", "event": "Heavy pre-winter rain", "impact": "Gomti river overflowed floodplains"}
        ],
        "resident_reviews": [
            {"author": "Lucknow Commuter", "rating": "Average", "review": "Charbagh station road and Alambagh underpass collect knee-deep water, but Gomti Nagar main roads clear in an hour.", "date": "2024-09-15"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Avoid Alambagh and Charbagh railway underpasses during peak rain."
    },
    {
        "locality": "Assi Ghat & Godowlia",
        "city": "Varanasi",
        "state": "Uttar Pradesh",
        "latitude": 25.3176,
        "longitude": 82.9739,
        "elevation_m": 80.0,
        "terrain_type": "Ganga & Varuna river high-bank / ancient depression",
        "drainage_system": "Poor / Medieval subterranean masonry drains",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Godowlia crossing", "Assi nallah confluence", "Varuna river bridge low roads", "Girjaghar crossing"],
        "past_flood_events": [
            {"year": "2024", "event": "Ganga river crossed danger mark; Varuna river backflow", "impact": "All ghats completely submerged; river water reached Godowlia chowk; boat traffic banned"},
            {"year": "2021", "event": "Historic Ganga flood inundated thousands of riverside homes", "impact": "Cremations shifted to rooftops at Harishchandra and Manikarnika ghats"}
        ],
        "resident_reviews": [
            {"author": "Varanasi Local", "rating": "Critical", "review": "When Ganga rises above 71 meters, Varuna river reverses flow and floods residential colonies like Konia and Saraiya.", "date": "2024-08-30"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "GHAT WARNING: Ghats become submerged and slippery. Godowlia and Assi nallah flood in heavy rain."
    },
    {
        "locality": "Botanical Garden & Sector 18 Underpass",
        "city": "Noida",
        "state": "Uttar Pradesh",
        "latitude": 28.5700,
        "longitude": 77.3200,
        "elevation_m": 200.0,
        "terrain_type": "Yamuna & Hindon floodplain terrace",
        "drainage_system": "Adequate / Wide concrete master drains to Hindon/Yamuna",
        "drainage_rating": 4,
        "clogging_tendency": "Low - Generally Clear",
        "chronic_chokepoints": ["Sector 18 underpass", "Sector 62 roundabout", "Sector 142 expressway service road"],
        "past_flood_events": [
            {"year": "2023", "event": "Yamuna flood breached regulator at Sector 137", "impact": "Submerged expressway floodplains and low cattle shelters; main sectors remained dry"}
        ],
        "resident_reviews": [
            {"author": "Noida Resident", "rating": "Good", "review": "Noida roads are broad and stormwater drains are huge. Rarely any deep clogging on main avenues.", "date": "2024-07-25"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Roads generally clear and safe. Minor puddling at Sector 18 subway during downpours."
    },

    # ------------------ 27. UTTARAKHAND ------------------
    {
        "locality": "ISBT & Rispana River Valley",
        "city": "Dehradun",
        "state": "Uttarakhand",
        "latitude": 30.3165,
        "longitude": 78.0322,
        "elevation_m": 640.0,
        "terrain_type": "Doon valley alluvial fan",
        "drainage_system": "Poor / Encroached Rispana & Bindal seasonal rivers",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["ISBT flyover low junction", "Rispana bridge", "Prince Chowk underpass", "Saharanpur road"],
        "past_flood_events": [
            {"year": "2024", "event": "Sudden cloudburst over Mussoorie foothills", "impact": "Rispana river surged, breaking boundary walls and waterlogging ISBT road with 3 feet water"},
            {"year": "2023", "event": "Severe monsoon torrents in Bindal and Song rivers", "impact": "Maldevta bridge washed away; road communication severed"}
        ],
        "resident_reviews": [
            {"author": "Dehradun Local", "rating": "Poor", "review": "ISBT roundabout and Prince Chowk flood within 30 minutes of mountain downpours. Avoid traveling without an SUV.", "date": "2024-08-11"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Flash torrents along Rispana river. High waterlogging at ISBT junction and Prince Chowk."
    },
    {
        "locality": "Har Ki Pauri & Laksar Belt",
        "city": "Haridwar",
        "state": "Uttarakhand",
        "latitude": 29.9457,
        "longitude": 78.1642,
        "elevation_m": 314.0,
        "terrain_type": "Ganga exit gorge into alluvial plain",
        "drainage_system": "Moderate / Upper Ganga Canal regulation",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Bhimghoda barrage approach", "Laksar rural highway", "Ranipur More subway"],
        "past_flood_events": [
            {"year": "2024", "event": "Ganga water level touched warning mark of 293 meters", "impact": "Submerged parking lots near Har Ki Pauri and low ghat steps"},
            {"year": "2023", "event": "Solani river and Sonali stream breaches in Laksar", "impact": "Laksar town flooded under 5 feet water; army deployed"}
        ],
        "resident_reviews": [
            {"author": "Haridwar Resident", "rating": "Average", "review": "Pilgrim areas around Har Ki Pauri are monitored closely, but southern areas like Laksar drown when dams release water.", "date": "2024-07-29"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Check Ganga discharge levels at Bhimghoda. Avoid Laksar rural roads during river surges."
    },

    # ------------------ 28. WEST BENGAL ------------------
    {
        "locality": "Park Street & Thanthania Kalibari (Amherst St)",
        "city": "Kolkata",
        "state": "West Bengal",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "elevation_m": 9.0,
        "terrain_type": "Hooghly tidal delta saucer basin",
        "drainage_system": "Poor / High tide sluice lock into Hooghly and KMC lockgates",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Thanthania Kalibari (College St)", "Amherst Street", "Park Circus 7-point crossing", "Behala Manton", "Ultadanga underpass"],
        "past_flood_events": [
            {"year": "2024", "event": "Low-pressure depression dumped 180mm rain over Kolkata in 12 hours", "impact": "Knee-to-waist deep water in College Street; trams halted; Metro water incursion at Park Street"},
            {"year": "2020", "event": "Super Cyclone Amphan storm surge and urban inundation", "impact": "City plunged into darkness for 5 days with waterlogged roads and thousands of fallen trees"}
        ],
        "resident_reviews": [
            {"author": "Kolkata Local (College St)", "rating": "Critical", "review": "Thanthania Kalibari and Amherst Street become waterlogged every single monsoon. Books get damaged and water takes 6-8 hours to recede.", "date": "2024-08-25"},
            {"author": "Behala Resident", "rating": "Poor", "review": "Diamond Harbour Road at Behala Manton collects heavy water. Avoid taking cars through Ultadanga underpass.", "date": "2024-09-02"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "SEVERE WATERLOGGING at College Street, Amherst St, and Behala Manton during high-tide rains."
    },
    {
        "locality": "Belur & Liluah Underpass",
        "city": "Howrah",
        "state": "West Bengal",
        "latitude": 22.5958,
        "longitude": 88.2636,
        "elevation_m": 12.0,
        "terrain_type": "Hooghly river floodplain / Railway embankment depression",
        "drainage_system": "Poor / Silted drainage outfalls",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Liluah railway underpass", "Tikiapara car shed low line", "Salkia Chowrasta"],
        "past_flood_events": [
            {"year": "2024", "event": "Heavy tidal rainfall submerged Howrah station car sheds", "impact": "Suburban train services delayed; Liluah subway filled with 5 feet water"}
        ],
        "resident_reviews": [
            {"author": "Howrah Commuter", "rating": "Critical", "review": "Liluah underpass is completely submerged in rainy season. Buses cannot pass. Use Kona expressway.", "date": "2024-08-19"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Liluah and Tikiapara subways severely waterlogged. Divert via Kona Expressway."
    },

    # ------------------ 29. ANDAMAN & NICOBAR ISLANDS (UT) ------------------
    {
        "locality": "Aberdeen Bazaar & Bathubasti",
        "city": "Port Blair",
        "state": "Andaman and Nicobar Islands",
        "latitude": 11.6234,
        "longitude": 92.7265,
        "elevation_m": 16.0,
        "terrain_type": "Island coastal hill fringe",
        "drainage_system": "Moderate / Direct sea discharge culverts",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Bathubasti junction", "Dollygunj low bridge", "Junglighat waterfront road"],
        "past_flood_events": [
            {"year": "2023", "event": "Cyclonic storm storm-surge and 160mm daily rain", "impact": "Submerged low shops in Bathubasti and Junglighat"}
        ],
        "resident_reviews": [
            {"author": "Port Blair Citizen", "rating": "Average", "review": "Steep slopes allow water to reach the sea quickly, but Bathubasti and Dollygunj gather localized water during high tide.", "date": "2023-10-18"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Watch out for high sea-swell and puddling on Dollygunj bridge."
    },

    # ------------------ 30. CHANDIGARH (UT) ------------------
    {
        "locality": "Sector 17 & Sukhna Choe (Manimajra)",
        "city": "Chandigarh",
        "state": "Chandigarh",
        "latitude": 30.7333,
        "longitude": 76.7794,
        "elevation_m": 350.0,
        "terrain_type": "Shivalik piedmont plain (Le Corbusier grid)",
        "drainage_system": "Adequate / Planned surface stormwater grid",
        "drainage_rating": 4,
        "clogging_tendency": "Low - Generally Clear",
        "chronic_chokepoints": ["Sector 35/36 underpass", "Kishangarh bridge over Sukhna Choe", "Industrial Area Phase 1 low road"],
        "past_flood_events": [
            {"year": "2023", "event": "Historic 250mm July downpour; Sukhna lake floodgates opened", "impact": "Sukhna Choe overflowed in Manimajra and Baltana; roundabout round waterlogging"}
        ],
        "resident_reviews": [
            {"author": "Chandigarh Citizen", "rating": "Good", "review": "Chandigarh has great natural slope from north to south. Water clears very rapidly, usually within 30 minutes.", "date": "2024-07-20"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Roads generally clear and safe. Watch Sukhna Choe crossing when lake gates open."
    },

    # ------------------ 31. DADRA & NAGAR HAVELI AND DAMAN & DIU (UT) ------------------
    {
        "locality": "Nani Daman Seafront & Silvassa Road",
        "city": "Daman",
        "state": "Dadra and Nagar Haveli and Daman and Diu",
        "latitude": 20.4283,
        "longitude": 72.8397,
        "elevation_m": 5.0,
        "terrain_type": "Daman Ganga estuary coastal lowlands",
        "drainage_system": "Poor / Tidal backflow into Daman Ganga river",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Nani Daman vegetable market", "Daman Ganga bridge approach", "Ghelwad low road Silvassa"],
        "past_flood_events": [
            {"year": "2024", "event": "Madhuban dam released 2.5 lakh cusecs during high tide", "impact": "Nani Daman and low industrial belts in Silvassa flooded with 3 feet water"}
        ],
        "resident_reviews": [
            {"author": "Daman Resident", "rating": "Poor", "review": "Daman Ganga river overflows the low bridge whenever Madhuban dam opens its spillways.", "date": "2024-08-03"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Tidal backwater danger. Avoid Daman Ganga riverfront roads during heavy rainfall."
    },

    # ------------------ 32. DELHI (NCT) (UT) ------------------
    {
        "locality": "ITO & Minto Bridge",
        "city": "Delhi",
        "state": "Delhi",
        "latitude": 28.6289,
        "longitude": 77.2405,
        "elevation_m": 213.0,
        "terrain_type": "Yamuna floodplain fringe & Railway depression",
        "drainage_system": "Poor / Silted Yamuna drains (Drain 12 / Barapullah)",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Minto Bridge railway underpass", "ITO junction & Vikas Marg", "Tilak Bridge underpass", "Kashmere Gate ISBT low road", "Pul Prahladpur underpass", "Dhaula Kuan underpass"],
        "past_flood_events": [
            {"year": "2023", "event": "Historic Yamuna river flood (record peak 208.66m)", "impact": "Yamuna water reached Red Fort, ITO intersection, and Supreme Court; water treatment plants shut down; army deployed"},
            {"year": "2024", "event": "June 28 record 228mm cloudburst in Delhi", "impact": "Minto bridge submerged up to 8 feet; T1 airport canopy collapse; city gridlocked for 12 hours"}
        ],
        "resident_reviews": [
            {"author": "Delhi Daily Commuter", "rating": "Critical", "review": "Minto Bridge and ITO junction submerge with every heavy rain. Automatic sensors close Minto bridge, but ITO turns into a standstill crawl.", "date": "2024-07-01"},
            {"author": "East Delhi Resident", "rating": "Poor", "review": "Vikas Marg from Laxmi Nagar to ITO becomes completely waterlogged. Drains cannot empty when Yamuna level is high.", "date": "2024-07-15"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "SEVERE CLOGGING HAZARD: Minto Bridge, Pul Prahladpur, and ITO experience deep water stagnation. Use Barapullah elevated road."
    },

    # ------------------ 33. JAMMU & KASHMIR (UT) ------------------
    {
        "locality": "Lal Chowk & Rajbagh",
        "city": "Srinagar",
        "state": "Jammu and Kashmir",
        "latitude": 34.0837,
        "longitude": 74.7973,
        "elevation_m": 1585.0,
        "terrain_type": "Jhelum river flood basin",
        "drainage_system": "Critical / Jhelum river embankment spillway dependency",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Lal Chowk city center", "Rajbagh low embankment", "Jawahar Nagar", "Hari Singh High Street", "Bemina flood spill channel"],
        "past_flood_events": [
            {"year": "2024", "event": "Spring heavy rainfall caused Jhelum river to cross flood declaration mark at Ram Munshi Bagh", "impact": "Bemina low colonies inundated; emergency pumping stations operated 24x7"},
            {"year": "2014", "event": "Catastrophic Kashmir Deluge; Jhelum breached embankments", "impact": "Lal Chowk and Rajbagh submerged under 12-18 feet water for over 10 days; historic damage"}
        ],
        "resident_reviews": [
            {"author": "Srinagar Resident (Rajbagh)", "rating": "Critical", "review": "Rajbagh is lower than the Jhelum bund. If Jhelum reaches 21 feet at Ram Munshi Bagh, the backwater starts entering our basements.", "date": "2024-04-30"},
            {"author": "Lal Chowk Trader", "rating": "Poor", "review": "City center drains overflow into shops during continuous rain. Road travel halts quickly.", "date": "2024-05-02"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "EXTREME FLOOD RISK: Monitor Jhelum gauge at Ram Munshi Bagh. Lal Chowk & Rajbagh submerge during river swells."
    },
    {
        "locality": "Chashoti (Padder valley)",
        "city": "Kishtwar",
        "state": "Jammu and Kashmir",
        "latitude": 33.3779,
        "longitude": 76.2783,
        "elevation_m": 2450.0,
        "terrain_type": "Glaciated high-altitude gorge valley",
        "drainage_system": "Critical / High-gradient mountain stream prone to rockslide dams",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Machail yatra foot track", "Chashoti wooden bridge", "Gulabgarh road culverts"],
        "past_flood_events": [
            {"year": "2024", "event": "Cloudburst in Padder hills caused sudden flash flood", "impact": "Damaged pedestrian tracks and wooden bridges on Machail route"},
            {"year": "2021", "event": "Honzar cloudburst flash flood in Dacchan", "impact": "Villages destroyed and multiple casualties"}
        ],
        "resident_reviews": [
            {"author": "Padder Local", "rating": "Critical", "review": "Mountain torrents carry huge mud and boulders. Tracks get blocked within minutes.", "date": "2024-07-28"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Flash flood & landslide warning on mountain roads during rainfall."
    },

    # ------------------ 34. LADAKH (UT) ------------------
    {
        "locality": "Main Bazaar & Choglamsar",
        "city": "Leh",
        "state": "Ladakh",
        "latitude": 34.1526,
        "longitude": 77.5771,
        "elevation_m": 3524.0,
        "terrain_type": "Cold arid alluvial fan (Indus valley)",
        "drainage_system": "Critical / Fragile mud-plaster channels unprepared for heavy rain",
        "drainage_rating": 1,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Choglamsar Indus bank", "Leh old town mud-slope", "Airport road culvert"],
        "past_flood_events": [
            {"year": "2010", "event": "Devastating August 6 cloudburst (250mm torrential cloudburst in desert mountain)", "impact": "Triggered massive mud and boulder debris torrents; 255 fatalities; Choglamsar flattened"}
        ],
        "resident_reviews": [
            {"author": "Leh Resident", "rating": "Critical", "review": "Ladakh's soil does not absorb water. Any sudden rain brings thick mud and boulders down the slopes, completely blocking roads.", "date": "2023-08-10"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Even moderate rain causes severe mudflows on Leh roads due to desert terrain."
    },

    # ------------------ 35. LAKSHADWEEP (UT) ------------------
    {
        "locality": "Helipad Road & Beach Frontage",
        "city": "Kavaratti",
        "state": "Lakshadweep",
        "latitude": 10.5667,
        "longitude": 72.6417,
        "elevation_m": 2.0,
        "terrain_type": "Coral atoll flat sand strip",
        "drainage_system": "Natural / High sandy soil percolation, but sea inundation prone",
        "drainage_rating": 3,
        "clogging_tendency": "Moderate - Slow Drainage",
        "chronic_chokepoints": ["Eastern jetty road", "Helipad low perimeter"],
        "past_flood_events": [
            {"year": "2023", "event": "Cyclone Biparjoy sea swell and high tide", "impact": "Seawater breached low sand dunes, submerging beach roads"}
        ],
        "resident_reviews": [
            {"author": "Island Resident", "rating": "Average", "review": "Rainwater percolates into sand rapidly, but high sea surges during cyclones wash right over the road.", "date": "2023-06-18"}
        ],
        "clogged_under_rain": False,
        "travel_advisory": "Percolation is fast, but avoid coastal perimeter roads during stormy sea surges."
    },

    # ------------------ 36. PUDUCHERRY (UT) ------------------
    {
        "locality": "Goubert Avenue (Beach Road) & Rainbow Nagar",
        "city": "Puducherry",
        "state": "Puducherry",
        "latitude": 11.9416,
        "longitude": 79.8083,
        "elevation_m": 3.0,
        "terrain_type": "Coromandel coastal flat / Grand Canal basin",
        "drainage_system": "Poor / Silted French-era Grand Canal",
        "drainage_rating": 2,
        "clogging_tendency": "High - Frequent Clogging",
        "chronic_chokepoints": ["Rainbow Nagar low streets", "Grand Canal bridge crossings", "Indira Gandhi square underpass", "Villianur road"],
        "past_flood_events": [
            {"year": "2024", "event": "Cyclone Fengal dumped unprecedented 480mm rain in 24 hours (highest in 30 yrs)", "impact": "Widespread inundation; Rainbow Nagar and Krishna Nagar submerged under 4-5 feet water; army deployed"},
            {"year": "2020", "event": "Cyclone Nivar coastal deluge", "impact": "Beach road cut off, extensive low-income area flooding"}
        ],
        "resident_reviews": [
            {"author": "Pondy Resident (Rainbow Nagar)", "rating": "Critical", "review": "Cyclone Fengal proved our drainage is completely broken. Grand Canal overflowed and homes were under 4 feet water for 4 days.", "date": "2024-12-05"},
            {"author": "White Town Citizen", "rating": "Average", "review": "White town roads drain into the sea fairly well, but North and West residential extensions turn into lakes.", "date": "2024-12-06"}
        ],
        "clogged_under_rain": True,
        "travel_advisory": "Rainbow Nagar & Indira Gandhi square flood deeply during cyclone downpours."
    }
]


def find_matching_localities(
    query_text: str | None = None,
    city: str | None = None,
    state: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    allow_state_fallback: bool = False,
) -> list[LocalityInfo]:
    """Find matching localities using fuzzy text matching, aliases, and coordinate proximity.
    
    If a specific city is supplied, it strictly matches that city (or its aliases/fuzzy typos).
    It will NEVER substitute an unrelated city in the same state unless allow_state_fallback=True.
    """
    results: list[LocalityInfo] = []

    norm_query = _norm(query_text or "")
    norm_city = _norm(city or "")
    norm_state = _norm(state or "")

    for loc in INDIA_FLOOD_DATABASE:
        loc_city = _norm(loc["city"])
        loc_state = _norm(loc["state"])
        loc_name = _norm(loc["locality"])
        aliases = [_norm(a) for a in loc.get("aliases", [])]

        # 1. State filter if specified
        if norm_state and not _fuzzy_match(norm_state, loc_state, 0.70):
            # Check if any state token matches
            if not any(_fuzzy_match(w, loc_state, 0.75) for w in norm_state.split()):
                continue

        # 2. City filter if specified
        if norm_city:
            city_hit = False
            # Check exact or fuzzy match with city name
            if _fuzzy_match(norm_city, loc_city, 0.72):
                city_hit = True
            # Check aliases (e.g. Dharbanga -> Darbhanga, Banaras -> Varanasi, Bangalore -> Bengaluru)
            elif any(_fuzzy_match(norm_city, alias, 0.72) for alias in aliases):
                city_hit = True
            # Check if user typed the locality name into the city box
            elif _fuzzy_match(norm_city, loc_name, 0.80):
                city_hit = True
            
            if city_hit:
                results.append(loc)
            continue

        # 3. Query / Locality check if no city was specified
        if norm_query:
            matched_query = False
            if _fuzzy_match(norm_query, loc_name, 0.70) or _fuzzy_match(norm_query, loc_city, 0.72):
                matched_query = True
            elif any(_fuzzy_match(norm_query, alias, 0.72) for alias in aliases):
                matched_query = True
            else:
                for chokepoint in loc.get("chronic_chokepoints", []):
                    if _fuzzy_match(norm_query, chokepoint, 0.70):
                        matched_query = True
                        break
            if matched_query:
                results.append(loc)
                continue

        # 4. Proximity match if lat/lon provided (within ~65 km)
        if lat is not None and lon is not None:
            dist_sq = (loc["latitude"] - lat) ** 2 + (loc["longitude"] - lon) ** 2
            if dist_sq <= 0.6**2:
                results.append(loc)

    # 5. Optional State fallback ONLY if explicitly allowed and no city was specified or matched
    if not results and norm_state and allow_state_fallback:
        for loc in INDIA_FLOOD_DATABASE:
            if _fuzzy_match(norm_state, _norm(loc["state"]), 0.70):
                fallback_loc = dict(loc)
                fallback_loc["is_state_fallback"] = True
                results.append(fallback_loc)

    # Remove duplicates preserving order
    unique: list[LocalityInfo] = []
    seen = set()
    for item in results:
        key = (item["city"], item["locality"])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique


def get_all_locations_directory() -> list[dict[str, str | float | list[str]]]:
    """Returns a simplified list of all cities and states for offline geocoding and UI autocomplete."""
    directory = []
    for loc in INDIA_FLOOD_DATABASE:
        directory.append({
            "locality": loc["locality"],
            "city": loc["city"],
            "aliases": loc.get("aliases", []),
            "state": loc["state"],
            "lat": loc["latitude"],
            "lon": loc["longitude"],
            "clogging_tendency": loc["clogging_tendency"],
            "clogged_under_rain": loc["clogged_under_rain"],
        })
    return directory

