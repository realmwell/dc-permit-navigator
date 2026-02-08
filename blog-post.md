# I Cataloged Every DC Permit I Could Find. Here's What I Learned.

Washington DC has a permit for keeping pigeons.

It also has a permit for keeping exotic animals, a separate permit for animal disease prevention, and a permit for animal hobbies — all from the same agency (DC Health), each requiring a separate application. And none of them are listed in the same place.

This is the story of what happens when you try to build a comprehensive database of every permit, license, and certification that the DC government offers to the public. I found 103 of them across 16 agencies. I probably missed some. Nobody — including the DC government — seems to have a complete list.

## The Motivation

I believe that government should be making it faster and easier to grant permits. Every day a permit is delayed is a day a small business can't open its doors, a homeowner can't start their renovation, or a neighborhood can't throw a block party. The permitting system isn't just bureaucracy — it's the gateway between citizens and the things they want to do in their city.

Before you can fix a system, you need to understand it. So I set out to catalog every DC permit I could find, and then built an AI chatbot to help people navigate them.

## What I Found: 103 Permits, 16 Agencies, 16 Portals

The first thing that hits you is the sheer fragmentation.

Want to open a restaurant in DC? Here's your permit shopping list:

1. **Basic Business License** — DLCP (formerly half of DCRA)
2. **Building Permit** — DOB (formerly the other half of DCRA)
3. **Certificate of Occupancy** — DOB
4. **Food Service Establishment License** — DC Health ($280-$560)
5. **Food Handler Permits** — DC Health ($10/employee)
6. **Certified Food Protection Manager** — DC Health (~$150 exam)
7. **On-Premises Alcohol License** — ABCA (60-120 day process)
8. **Sidewalk Cafe Permit** — DDOT (through TOPS)
9. **Certificate of Use for Sidewalk Cafe** — DOB
10. **Fire Code Operational Permit** — FEMS
11. **Possibly**: Historic Preservation Review (Office of Planning), Zoning Variance (BZA), Stormwater Management Plan (DOEE), Erosion & Sediment Control (DOEE)

That's potentially 11+ permits from 7 different agencies, each with its own website, its own application portal, and its own timeline. Nobody hands you this list. You discover it one painful permit at a time.

## Insight #1: The Agency Name Problem

If you're new to DC permitting, good luck figuring out which agency to call.

DCRA (Department of Consumer and Regulatory Affairs) was split into **DOB** (Department of Buildings) and **DLCP** (Department of Licensing and Consumer Protection). But many URLs still point to dcra.dc.gov. The old Permit Wizard lives at permitwizard.dcra.dc.gov. Some Google results reference DCRA pages that now redirect (or don't).

ABRA (Alcoholic Beverage Regulation Administration) became **ABCA** (Alcoholic Beverage and Cannabis Administration) when cannabis licensing was added. DDOE became **DOEE**. The Office of Zoning is sometimes referenced as "DCOZ" and sometimes just "OZ."

For a resident trying to find the right agency, this is genuinely confusing. Search for "DCRA building permit" and you'll find a mix of current DOB pages and outdated DCRA references.

## Insight #2: Processing Times Are a Black Box

Of the 103 permits I cataloged, the vast majority list processing time as "varies." A few notable exceptions:

- **Marriage License**: Same day (DC gets this right)
- **Parade Permit**: Minimum 15 business days
- **Asbestos Abatement**: Minimum 10 working days advance notification
- **Driver's License**: Same day if you pass the test
- **Alcohol License**: 60-120 days typical

But for building permits? "Varies." Food service license? "Varies." Business license? "Varies." Zoning variance? "Several months."

This lack of transparency makes it impossible for applicants to plan. A restaurant owner investing hundreds of thousands of dollars can't even get a ballpark estimate of when they'll be able to open.

## Insight #3: The Fee Spectrum

Permit fees range from free to $8,000:

- **Free**: First Amendment assembly notification, HPRB concept review
- **$10**: Food handler's permit (per person)
- **$13**: Firearms registration (per firearm)
- **$23**: Birth certificate copy
- **$35**: Marriage license, residential parking permit
- **$47**: Driver's license (8-year)
- **$50-$135**: Fence/driveway permits
- **$150**: Fire marshal event review
- **$280-$560**: Food service establishment license
- **$8,000**: Medical cannabis retailer license application ($2,000 for social equity applicants)

Many permits don't publish fees online at all, which means you can't even budget without calling the agency first.

## Insight #4: Digital Adoption Is Wildly Uneven

DDOT's TOPS (Transportation Online Permitting System) has been running since 2012. DOB has the Permit Wizard and Citizen Access Portal. These are functional, if not beautiful.

But then you have agencies where the "application process" is: download a PDF, print it, fill it out by hand, bring it to a specific office during specific hours (8:30am-4:15pm, closed Thursdays at some offices), and wait.

DC Health recently stopped accepting paper applications for food permits — a good step. But ABCA still accepts cannabis license applications by mail. The HPRB concept review process requires emailing a completed form to an agency email address.

There's no unified permitting portal. No single sign-on. No dashboard where you can see all your pending permits across agencies.

## Insight #5: The Permits You Didn't Know You Needed

Some surprises from the database:

- **Pigeon Coop Permit** (DC Health) — Yes, you need a permit to keep pigeons
- **Tree Removal Permit** (DDOT Urban Forestry) — That tree between the sidewalk and the curb? You can't touch it without DDOT permission
- **Retaining Wall Permit** (DOB) — Walls over 4 feet from footing to top need a building permit
- **Pop-Up Permit** (DOB) — A streamlined 1-year C of O for temporarily occupying a vacant building
- **Commercial Lifestyle License** (ABCA) — For drinking in the common areas of mixed-use developments
- **Athlete Agent License** (DLCP) — Required if you represent athletes in DC
- **Combat Sports License** (DLCP) — For fighters, promoters, and referees

## Building the Chatbot

I built an AI chatbot to make this database useful — because a 103-row JSON file isn't exactly user-friendly.

The architecture is deliberately cheap. The entire stack costs under $1/month at low usage:

- **Frontend**: Static HTML on S3 + CloudFront (essentially free)
- **API**: Lambda Function URL (free — no API Gateway)
- **Vector search**: FAISS index loaded in Lambda memory ($0)
- **Embeddings**: Amazon Bedrock Titan v2 (~$0.000004 per query)
- **LLM**: Amazon Bedrock Claude Haiku (~$0.001 per query)
- **Total per query**: About a tenth of a cent

The FAISS index is pre-built at deploy time from the permit database. At query time, the user's question is embedded, matched against the most relevant permits, and Claude Haiku generates a natural language answer with links and next steps.

## What Should Change

Building this database reinforced my conviction that DC's permitting system needs reform:

1. **One portal to rule them all** — There should be a single DC.gov permits portal where you can search, apply for, and track ALL permits across ALL agencies. The current approach of 16 separate systems is a tax on residents' time.

2. **Publish processing times** — Every permit should have a published average processing time, updated monthly. "Varies" is not an answer.

3. **Permit bundles** — Common activities (open a restaurant, renovate a home, host an event) should have curated bundles that tell you every permit you need from every agency, with a single timeline.

4. **Publish fees online** — Every permit fee should be listed on the agency's website. Making people call or visit an office just to learn the cost is unacceptable in 2026.

5. **Name consistency** — Pick a name for the agency and use it everywhere. Redirect old URLs. Update Google results. Stop confusing people with DCRA/DOB/DLCP.

## Try It

The chatbot is live at [URL]. The full permit database and source code are open source on GitHub at [URL].

If you know of a DC permit I missed, please open an issue. This database should be as complete as possible.

---

*This project is not affiliated with or endorsed by the DC government. Always verify permit requirements directly with the issuing agency.*
