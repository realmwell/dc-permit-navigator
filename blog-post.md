# I Cataloged Every DC Permit I Could Find. Here's What the Data Reveals.

Washington DC has a permit for keeping pigeons.

It also has a permit for keeping exotic animals, a separate permit for animal disease prevention, and a permit for animal hobbies — all from the same agency (DC Health), each requiring a separate application. And none of them are listed in the same place.

I set out to build a comprehensive database of every permit, license, and certification that the DC government offers to the public. I found 103 of them across 16 agencies. I probably missed some. Nobody — including the DC government — seems to have a complete list.

So I built the [DC Permit Navigator](https://github.com/realmwell/dc-permit-navigator), a free, open-source chatbot backed by a hand-curated database of every DC permit I could find. You ask a question — "What do I need to open a restaurant?" — and it tells you every permit, from every agency, with fees, requirements, and application links. No login, no paywall, no ads.

Here's what the data shows — and what it says about how DC treats the people who want to build things in this city.

## 103 permits. 16 agencies. 16 portals.

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

The permit database breaks down into 16 categories: Building & Construction (15 permits), Alcohol & Cannabis (13), Professional & Occupational Licenses (13), Public Space & Transportation (11), Parking & Driving (8), Environmental (8), Events & Entertainment (6), Food & Health (6), Animal Permits (5), Business Licenses (4), Vital Records (4), Fire & Safety (3), Historic Preservation (2), Zoning (2), Health Professions (1), and Firearms (1).

## The agency name problem

If you're new to DC permitting, good luck figuring out which agency to call.

DCRA (Department of Consumer and Regulatory Affairs) was split into **DOB** (Department of Buildings) and **DLCP** (Department of Licensing and Consumer Protection). But many URLs still point to dcra.dc.gov. The Permit Wizard lives at permitwizard.dcra.dc.gov. Google results reference DCRA pages that now redirect — or don't.

ABRA (Alcoholic Beverage Regulation Administration) became **ABCA** (Alcoholic Beverage and Cannabis Administration) when cannabis licensing was added to its portfolio. DDOE became **DOEE**. The Office of Zoning is sometimes referenced as DCOZ and sometimes just OZ.

For a resident trying to find the right agency, this is genuinely confusing. Search for "DCRA building permit" today and you'll get a mix of current DOB pages and outdated DCRA references. The system assumes you already know the institutional history.

## Processing times are a black box

Of the 103 permits I cataloged, the vast majority list processing time as "varies." The exceptions stand out precisely because they're exceptions:

- **Marriage License**: Same day. DC gets this right.
- **Parade Permit**: Minimum 15 business days
- **Asbestos Abatement**: Minimum 10 working days advance notification
- **Driver's License**: Same day if you pass the test
- **Alcohol License**: 60-120 days typical

But for building permits? "Varies." Food service license? "Varies." Business license? "Varies." Zoning variance? "Several months."

This lack of transparency makes it impossible for applicants to plan. A restaurant owner investing hundreds of thousands of dollars in a buildout can't even get a ballpark estimate of when they'll be able to open. A homeowner can't tell their contractor when to start work. An event organizer can't set a date.

The contrast with marriage licenses is instructive. You walk into DC Superior Court, pay $35, and walk out married. Same day. If DC can process a legal contract that binds two people for life in an afternoon, why does a fence permit take weeks?

## The fee spectrum

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

Many permits don't publish fees online at all. You can't even budget without calling the agency, assuming you can find the right phone number, during their office hours, which may or may not be listed on their website.

## Digital adoption is wildly uneven

DDOT's TOPS (Transportation Online Permitting System) has been running since 2012. DOB has the Permit Wizard and Citizen Access Portal. These are functional, if not elegant.

Then you have agencies where the "application process" is: download a PDF, print it, fill it out by hand, bring it to a specific office during specific hours (8:30am-4:15pm, closed Thursdays at some locations), and wait.

DC Health recently stopped accepting paper applications for food permits — a good step. But ABCA still accepts cannabis license applications by mail. The HPRB concept review process requires emailing a completed form to a generic agency email address. The vending license from DLCP requires an in-person appointment.

There's no unified permitting portal. No single sign-on. No dashboard where you can see all your pending permits across agencies. Sixteen agencies, sixteen separate systems, sixteen sets of credentials.

## The permits you didn't know you needed

Some surprises from the database:

- **Pigeon Coop Permit** (DC Health) — Yes, you need a permit to keep pigeons.
- **Tree Removal Permit** (DDOT Urban Forestry) — That tree between the sidewalk and the curb? You can't touch it without DDOT permission.
- **Retaining Wall Permit** (DOB) — Walls over 4 feet from footing to top need a building permit.
- **Pop-Up Permit** (DOB) — A streamlined 1-year Certificate of Occupancy for temporarily using a vacant building. One of the few permits that seems designed to reduce friction.
- **Commercial Lifestyle License** (ABCA) — For drinking alcohol in the common areas of mixed-use developments. The kind of specific permit that could only exist in a city with The Wharf.
- **Athlete Agent License** (DLCP) — Required if you represent athletes in DC.
- **Combat Sports License** (DLCP) — Separate licenses for fighters, promoters, referees, and judges.

The system assumes you know what to ask for. Nobody tells you that your retaining wall needs a building permit until a neighbor calls DOB. Nobody mentions the erosion control plan until you're mid-demolition. The interconnections between permits — a single project touching DOB, DOEE, DDOT, and HPO simultaneously — are invisible unless you've done it before.

## How I built it (for less than $5/month)

The chatbot runs on a serverless AWS stack that mirrors what I used for the [DC Bus Delay Tracker](https://github.com/realmwell/dc-bus-delay-tracker): a single Lambda function, S3 for static hosting, CloudFront for CDN, and no database. The only new ingredient is Amazon Bedrock for the AI components.

The permit database is embedded into a vector index at deploy time using Titan Embeddings v2, stored as a binary file in S3, and loaded into Lambda memory on cold start. At query time, your question gets embedded into the same vector space, matched against the most relevant permits via cosine similarity, and those permits are passed as context to Claude Haiku, which generates a natural language answer.

The key architectural choice was skipping API Gateway entirely. Lambda Function URLs are free, and for a proof of concept with a daily query cap, they work perfectly. I also skipped managed vector databases — Aurora Serverless v2 has a $43/month minimum, OpenSearch Serverless starts at $691/month. A 103-document index fits comfortably in Lambda's 512MB memory allocation.

Total cost per query: about a tenth of a cent. At 50 queries per day — more than this proof of concept will likely see — the monthly bill comes to roughly $2.

I built it with [Claude Code](https://claude.ai/claude-code) as a pair programming partner. It handled everything from the SAM template to the FAISS index builder to the frontend chat interface. The permit database itself was the labor-intensive part — manually compiled from dc.gov and individual agency websites, cross-referenced and structured. That's the kind of work no AI can fully automate yet: navigating 16 different government portals, reconciling outdated URLs, and making judgment calls about what counts as a "permit."

## What should change

Building this database reinforced something I already believed: DC's permitting system needs structural reform. Five specific things:

**One portal.** There should be a single DC.gov permits page where you can search, apply for, and track every permit across every agency. The current approach of 16 separate systems is a tax on residents' time and a barrier to economic activity.

**Published processing times.** Every permit should have a published average processing time, updated monthly. "Varies" is not an answer. If marriage licenses can be same-day, processing time benchmarks can exist for everything else.

**Permit bundles.** Common activities — open a restaurant, renovate a home, host a street event — should have curated bundles that tell you every permit you need from every agency, with a single combined timeline. The restaurant owner shouldn't have to discover permit #7 after permits 1-6 are already in process.

**Published fees.** Every permit fee should be listed on the agency's website. Making people call or visit an office to learn the cost is unacceptable in 2026.

**Name consistency.** Pick a name for the agency and use it everywhere. Redirect old URLs. Update search results. Stop confusing people with DCRA/DOB/DLCP.

## Try it

The navigator is live at [URL]. The full permit database — all 103 permits with agencies, fees, requirements, and application links — is browsable on the site without needing to use the chatbot. The source code and data are open on [GitHub](https://github.com/realmwell/dc-permit-navigator).

If you know of a DC permit I missed, please open an issue. This database should be as complete as possible.

---

*Max Greenberg builds data tools in Washington, DC. The DC Permit Navigator is open source and free to use.*
