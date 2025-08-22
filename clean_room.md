Unified Customer Journey Insights Across Adtech Clean Rooms

1. The Attribution Challenge in AdTech

State (Last-Touch Attribution Problem):

Most teams still rely on last-touch attribution (crediting only the final touchpoint).

Reality:

Customers interact across multiple channels (search, Meta, YouTube, etc.) before converting.

Problem:

Big platforms share only aggregated (not user-level) data.

This keeps the customer journey fragmented.

Outcome:

Teams cannot easily connect the dots across channels.

It’s difficult to give proper weighting to each channel.

2. Data Clean Rooms: Pros and Cons

Definition:

Secure environments where advertisers and platforms combine data for analysis, without revealing individual identities.

Examples:

Google Ads Data Hub (ADH)

Amazon Marketing Cloud (AMC)

Meta Clean Room

Benefits:

Enables multi-touch attribution and journey analysis within a single platform.

Privacy-safe (aggregation, anonymization, restricted queries).

Drawbacks:

Each clean room is tied to one platform.

If you use 20 platforms, you may need 20 separate clean rooms, with no interoperability.

3. How Companies Handle Cross-Platform Measurement
Neutral / Independent Clean Rooms

Vendors: LiveRamp, InfoSum, Habu, Snowflake

Objective: Serve as an aggregation layer for multiple platforms.

How: Use hashed IDs (email, phone) or universal IDs (RampID, UID 2.0) to unify identity across channels.

Example: LiveRamp pipelines join Google, Amazon, and Meta data using RampID.

Identity Resolution & MMPs

Vendors: AppsFlyer, Adjust, Branch

Solution: Use first-party identifiers (with consent) to connect ad exposures and conversions.

Example: AppsFlyer’s Privacy Cloud clean room claims cross-clean-room interoperability, enabling cross-platform attribution.

Case Studies (Financial Services & FinTech)

TSB Bank + InfoSum: Matched 5M bank customers with 50M radio listeners → 31% increase in new account applications.

Global FinTech + ITV Clean Room: Measured ad campaign incrementality → 18% increase in app downloads.

Learning: Privacy-safe matching enables cross-domain attribution (digital + offline media).

Walled Garden Partnerships

Snap + LiveRamp: One-click Snap data integration with other channels.

NBCU + Snowflake: Attribution across TV and digital behaviors.

Manual Alternative: Export aggregated results from Google ADH or Meta clean rooms, then ingest into a neutral environment for stitching.

Advanced Modeling

Marketing Mix Modeling (MMM): Uses aggregate spend/conversion data to estimate contribution across channels.

Hybrid Approach: Combine clean room outputs + MMM + controlled experiments to build a complete view.

4. Towards One Clean Room (Interoperability & Future)

Challenge:

Large platforms don’t link their clean rooms.

Industry Push:

Neutrality and interoperability (InfoSum, Snowflake, LiveRamp).

Trends:

Standards under development by IAB and W3C.

Vendors like Habu are creating cross-clean-room orchestration.

“The demand for standards is obvious to all.” — AppsFlyer Privacy Cloud.

5. Recommendations for FinTech Teams

Adopt an agnostic clean room (LiveRamp, InfoSum, Snowflake, Habu) as the central hub.

Gradually integrate platform clean rooms (e.g., pull aggregated ADH data → ingest into neutral hub).

Use identity resolution with hashed IDs or MMPs (AppsFlyer, Adjust).

Complement with MMM & experiments to fill blind spots.

Stay privacy-compliant with GDPR/CCPA by using anonymization, differential privacy, and consent-based identifiers.

6. Key Takeaways

Platform clean rooms (Meta, Google, YouTube) → Deep analysis, but siloed.

Independent clean rooms + identity resolution → Cross-platform unity.

FinTech firms with strong 1st-party data are best positioned to win.

No single “one clean room” today → Use a hub-and-spoke model with neutral clean rooms.

Future: Industry standards will enable true multi-platform clean rooms.


The Attribution Challenge in AdTech

Last-touch attribution (giving all credit to the final touchpoint) often misrepresents the true customer journey. In reality, customers may engage with multiple channels (search ads, social media, video, etc.) before converting. Relying solely on last-touch data overlooks earlier influences. Marketers – including those in FinTech – increasingly seek multi-touch attribution models that consider all steps of the customer journey for more accurate insight. The difficulty is that data from each marketing platform is siloed. Major ad platforms like Google (including YouTube) and Meta share only aggregated metrics, not user-level journey data, due to privacy restrictions. This makes it hard to connect the dots across channels and assign proper credit to each touchpoint
infosum.com
didomi.io
. In short, the customer journey is fragmented across walled gardens, and each platform tends to “grade its own homework” when reporting conversions
infosum.com
. This fragmentation has led to an industry push for better solutions.

Data Clean Rooms: Deeper Insights Within Silos

Data Clean Rooms have emerged as a key tool to bridge some of these gaps. A data clean room is a secure environment where an advertiser and a platform (or multiple partners) can combine data for analysis without exposing individual user identities
tealium.com
didomi.io
. For example, Google’s Ads Data Hub (ADH), Amazon’s Marketing Cloud (AMC), and Meta’s clean room solutions (often referred to as “Advanced Analytics” or similar) allow advertisers to upload their first-party data and join it with impression and click data inside the platform’s controlled environment
tealium.com
. This enables analysis of customer pathing and attribution within that platform. Marketers can perform tasks like frequency capping, better attribution modeling, and journey analysis inside each walled garden
tealium.com
. In fact, clean rooms can facilitate multi-touch attribution and journey analysis within a given ecosystem – for instance, Amazon’s and Google’s clean rooms let brands analyze the sequence of ad exposures and touchpoints for users in those platforms
tealium.com
. This is a big improvement in granularity and control compared to standard platform reports. Clean rooms are privacy-safe, using aggregation, anonymization, and query restrictions to ensure no raw personal data leaves the environment
didomi.io
didomi.io
.

However, a major limitation remains: each platform’s clean room only covers that platform’s data. If you advertise on 20 platforms, you might end up using 20 different clean rooms and still lack a unified customer journey view. These walled-garden clean rooms do not interoperate with each other – for example, Google’s ADH cannot directly connect with Amazon’s AMC, and neither will integrate with Meta’s clean room
reddit.com
. As one industry expert quipped, “Google’s DCR doesn’t work with Amazon’s & vice versa”
reddit.com
. In practice, this means the cross-platform insight gap persists – data remains siloed by platform, making it difficult to stitch together a consumer’s journey across Google, Facebook/Meta, YouTube, etc. (each platform only shows its piece of the puzzle)
tredence.com
. Marketers still can’t easily see that a customer, say, clicked a Google search ad, later saw a Meta ad, and finally converted after an email – at least not in one place.

How AdTech Teams Are Tackling Cross-Platform Journey Measurement

Leading marketing and adtech teams are attacking this problem through a combination of independent clean rooms, identity resolution, and advanced modeling. Here’s how companies are working to get a “whole picture” of the customer journey despite the data silos:

Using Independent/Neutral Clean Rooms: Rather than relying only on each media platform’s tools, many firms leverage neutral clean room providers (often part of the martech stack) that can ingest and join data from multiple sources. Vendors like LiveRamp, InfoSum, Habu, and Snowflake’s clean room solutions fall in this category
adexchanger.com
adexchanger.com
. These independent clean rooms don’t have “skin in the game” of any single media channel – they are designed to be interoperable across clouds and partners
adexchanger.com
infosum.com
. For example, Snowflake’s platform can work across AWS, Google Cloud, and Azure, allowing data from different sources to be collaborated on in one environment
adexchanger.com
. LiveRamp’s clean room emphasizes cross-media “collaboration in one place,” claiming to unify data from walled gardens, CTV, social, and more in a single de-duplicated view
liveramp.com
. Such solutions act as an aggregation layer: advertisers bring their first-party customer data, and the clean room can connect (often via privacy-safe matching) with data from Google, Meta, and others to produce joined insights. A Reddit discussion noted that LiveRamp, for instance, has pipelines to query data across Google, Amazon, and Meta’s environments by leveraging a common identifier (LiveRamp’s RampID)
reddit.com
. In one scenario, a brand used a LiveRamp ID to match users from Google Ads click data to their own CRM data, enabling cross-platform conversion tracking in a privacy-safe way
reddit.com
. The takeaway is that neutral clean rooms + identity resolution let advertisers do analysis across channels, not just within one walled garden. These systems often employ hashed email or phone-based IDs (or universal IDs like RampID, Unified ID 2.0, etc.) to find the same user across different platforms without exposing personal info.

Identity Resolution and MMPs: Some companies, especially in mobile and FinTech, use mobile measurement partners (MMPs) or identity providers to bridge platforms. For example, AppsFlyer – a leading MMP in mobile marketing – has launched its own data clean room as part of its Privacy Cloud, aiming to serve as an unbiased measurement layer across channels
tinuiti.com
tinuiti.com
. AppsFlyer’s clean room can take an advertiser’s data and match it with exposure data from multiple ad networks or platforms to close those “blind spots” in attribution
tinuiti.com
. The AppsFlyer team explicitly acknowledges that every walled garden having its own clean room “takes us right back to square one,” and says their solution is interoperable with other clean rooms and continuously adding integrations for a “complete cross-channel and cross-platform measurement”
tinuiti.com
. In practice, this means an independent party (like an MMP or identity partner) can ingest logs from Meta, Google, Twitter, etc., and use common user identifiers (with consent) to verify and unify measurement across them, rather than trusting each platform separately
reddit.com
reddit.com
. FinTech companies (which often have rich first-party data from logged-in users) commonly leverage such identity resolution: e.g. matching an ad click or impression to a customer email or ID in their database. This allows linking touchpoints from different channels to the same user. An important caveat is that privacy rules and platform policies often require doing this matching inside a clean room or via one-way hashed IDs, but the end result is a clearer map of the customer journey than any single platform could provide.

Case Study – Financial Services: In the financial industry (banks, card companies, fintech apps), there have been successful uses of neutral clean rooms to combine data across domains. For instance, TSB Bank (UK) collaborated with Global (a radio and media company) via an InfoSum clean room to match TSB’s 5 million banking customers with Global’s 50 million radio listeners
infosum.com
. This privacy-safe matching (no raw data exchanged) revealed which radio stations TSB’s customers listen to, informing ad spend and messaging. The campaign saw a 31% lift in new account applications, as TSB was able to optimize media across channels using these insights
infosum.com
. This is a great example of a cross-platform data collaboration – a bank’s first-party data combined with a media partner’s data – yielding a more complete picture of the customer and improving marketing outcomes. Another example: a global fintech company wanted to test a new ad campaign’s impact across channels. They used ITV’s clean-room-based planning platform (ITV is a UK TV broadcaster) to run a controlled incrementality experiment. By matching their user data with ITV’s audience data in the clean room, they measured an 18% lift in new app downloads from the campaign – giving confidence to roll it out widely
infosum.com
. These cases show FinTech and financial service marketers breaking data silos by partnering in neutral environments, tracking the same user across touchpoints (e.g. seeing that a user who saw a TV ad then visited a website or opened an account). Notably, even traditional media (radio, linear TV) is now being linked with digital outcomes through data clean rooms
infosum.com
, underscoring how a holistic customer journey view is achievable when data can be safely combined.

Walled Garden Cooperation: Some walled gardens are also opening up to third-party clean room collaborations to make life easier for advertisers. For example, Snap (Snapchat) partnered with LiveRamp to offer an “easy button” clean room integration
liveramp.com
. Instead of advertisers having to manually run separate analyses, Snap’s arrangement with LiveRamp lets brands directly and securely analyze Snap campaign data alongside their own data (or even alongside other media data) in LiveRamp’s environment
liveramp.com
. This kind of partnership hints at a future where one interface can query multiple platforms’ data in a governed way. Likewise, NBCUniversal built its own clean room (the NBCU Audience Insights Hub on Snowflake) and invited advertisers in – there, brands can match their data with NBC’s audience data and even do cross-platform attribution analysis (e.g. linking NBC’s TV exposure to digital behaviors) within that hub
didomi.io
. These efforts suggest that even the big media owners recognize advertisers need cross-channel views; they are cautiously enabling it by acting as facilitators (often using neutral tech under the hood, like Snowflake in NBC’s case
didomi.io
). Google and Meta themselves still keep tight control (their clean rooms don’t export user-level data), but they provide APIs or aggregated outputs that an advertiser can pull into a private data environment for further merging. For instance, an adtech team might run a query in Google ADH that yields aggregated, privacy-compliant stats for each user segment, then import those results into their own data warehouse to compare with Facebook results. It’s not a seamless process, but many advanced teams do “stitch” insights together this way as a workaround.

Advanced Modeling (MMM & Hybrid Approaches): In addition to data clean rooms, companies often complement their toolkit with Marketing Mix Modeling (MMM) and other statistical methods to infer cross-channel impact. MMM uses aggregate spend and conversion data across all channels (including those 20 platforms) to estimate the contribution of each channel. It doesn’t require user-level data, so it sidesteps the silo issue by working at a higher level. Modern marketers use MMM plus experiments (like turn-off tests for a given platform) to validate what each channel delivers. While MMM is outside the scope of clean rooms, it’s worth noting because no single clean room today gives a full 100% unified user-level view across every platform
tredence.com
. Clean rooms greatly improve multi-touch analysis where possible, but “they aren’t a silver bullet – data remains siloed across platforms, limiting a unified view” as one guide puts it
tredence.com
. Therefore, savvy teams use a hybrid measurement approach: they pull as much granular insight as they can from clean rooms and identity matching, then use modeling to fill in the gaps and ensure the overall picture is aligned. This way, they move toward holistic attribution even if a truly unified clean room for all platforms is not yet fully attainable.

Toward One Clean Room (Interoperability and Future Outlook)

Achieving “one clean room to rule them all” – a single environment covering all advertising platforms – is the ultimate vision, but it remains challenging under current conditions. The major ad platforms have little incentive to fully open up or interconnect their proprietary clean rooms (each is focused on its own ecosystem and data)
adexchanger.com
. This is why industry experts emphasize neutrality and interoperability as key. An ideal solution is a neutral clean room that can interface with any platform without locking the advertiser in
infosum.com
. InfoSum, for example, argues that clean rooms should be independent and not tied to a specific media owner or identifier, to allow true cross-platform data collaboration
infosum.com
infosum.com
. In 2025, we’re seeing progress: Snowflake’s data clean room infrastructure is gaining adoption because it’s cloud-agnostic and doesn’t come with a media business attached, making it easier to bring different datasets together
adexchanger.com
adexchanger.com
. LiveRamp and others also stress identity interoperability – the ability to match data using whatever common keys are available (emails, phone numbers, device IDs) rather than forcing everyone onto one ID system
infosum.com
infosum.com
.

Crucially, the industry is collaborating on standards to make multi-platform clean rooms feasible. The Interactive Advertising Bureau and W3C have working groups on clean room standards and privacy-enhancing tech, and major players are involved in these interoperability discussions
tinuiti.com
tinuiti.com
. “The need for standards and interoperability is clear and obvious to all,” as AppsFlyer’s GM of Privacy Cloud noted
tinuiti.com
. In time, this could mean easier data matching protocols and agreed rules that allow, say, a federated analysis across multiple clean rooms (where a query runs in each platform’s clean room and only aggregated results are combined). We’re not quite there yet, but some vendors are building connectors: for instance, Habu’s software can help coordinate analysis across different clean rooms, and we see partnerships like the one between Google and AWS clean rooms and independent software to bridge data
adexchanger.com
adexchanger.com
.

For an adtech team today, the pragmatic path to a unified view is to pick a primary clean room or data collaboration platform that supports multi-partner inputs, then integrate each ad platform through it one by one. This might mean working with providers that have integrations to Google ADH, Meta, YouTube, etc. (either via that provider’s API access or by bringing your aggregated results into the unified system). LiveRamp’s clean room, for example, touts “cross-media intelligence” that connects data from every screen and device in a de-duplicated view
liveramp.com
, and it achieves this by integrating with those walled gardens behind the scenes. In the Reddit forum, practitioners mentioned that some clean room providers will leverage deterministic matching across Google, Amazon, and Meta – essentially acting as a hub where all those data sets can be aligned on common user IDs
reddit.com
. Similarly, AppsFlyer’s clean room is “cloud platform-agnostic” and built to serve the marketer’s needs across channels (the legacy of MMPs is exactly cross-channel measurement)
tinuiti.com
. By using such a solution, an advertiser avoids having twenty completely separate analyses for 20 platforms – instead, they consolidate as much as possible in one neutral room. It’s not always a literal single clean room (since some data can’t leave its native platform), but it can feel like one virtual clean room via a central dashboard.

In summary, other companies are tackling multi-channel attribution with a mix of tools: they employ data clean rooms for granular analysis within each walled garden, and crucially, they bring the insights together using independent data collaboration platforms or identity resolution services to create a unified picture. FinTech firms, with their rich first-party data, are leveraging these methods to connect online ads to customer behaviors across channels, while big advertisers push for solutions that let them measure Facebook, Google, YouTube, and more side by side. Until true cross-platform clean rooms become standardized, the best approach is to use a neutral clean room provider that can interface with multiple platforms and to design your data strategy around privacy-compliant data matching. This gives your marketing team one quasi-unified environment to analyze the full customer journey. As evidence, companies that have done so – from retail banks to consumer brands – report improved marketing ROI and new insights once they break down those silos
infosum.com
infosum.com
. The landscape is evolving quickly, and cooperation between industry players (and initiatives by groups like IAB Tech Lab) is steadily moving us toward a future where a marketer truly can get a whole-picture view of the customer journey across all platforms in one place.




| Vendor / Approach                 | Capabilities                                                                 | Limitations                                                        | Reference |
|-----------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------|-----------|
| Google Ads Data Hub (ADH)         | Multi-touch attribution inside Google ecosystem (Search, YouTube, Display).   | Locked to Google ecosystem, no interoperability.                   | [24†L222-L230] |
| Amazon Marketing Cloud (AMC)      | Analyze Amazon ad exposures and conversions.                                  | Amazon-only, cannot merge natively with Google/Meta.                | [24†L222-L230] |
| Meta Clean Room                   | Combines Meta ads data with advertiser data.                                  | Meta-only visibility, siloed.                                       | [27†L265-L273] |
| LiveRamp (Neutral)                | Cross-platform collaboration, RampID identity resolution.                     | Relies on hashed IDs and partner integrations.                      | [10†L379-L388] |
| InfoSum (Neutral)                 | Privacy-safe “no data movement” model; used in FinTech/media cases.           | Requires partner cooperation; setup overhead.                       | [25†L218-L226] |
| Snowflake Clean Room              | Cloud-agnostic, supports NBCU attribution hub.                                | Needs ingestion from each platform clean room.                      | [17†L681-L689] |
| Habu                              | Orchestration across clean rooms; federated queries.                          | Still limited by each platform’s restrictions.                      | [3†L175-L183] |
| AppsFlyer Privacy Cloud (MMP)     | Mobile-first, interoperable across clean rooms.                               | Mostly mobile focus, still expanding to broader ecosystems.          | [30†L288-L296] |
| TSB Bank + InfoSum (Case Study)   | Bank matched 5M customers w/ 50M radio listeners → 31% lift.                  | Case-specific, needs collaboration.                                 | [25†L218-L226] |
| FinTech + ITV Clean Room (Case)   | Incrementality test → 18% app downloads lift.                                 | Limited to ITV partnership context.                                 | [25†L239-L247] |
| Snap + LiveRamp                   | One-click integration for Snap + other channels.                              | Restricted to Snap campaigns.                                       | [7†L237-L245] |
| NBCU + Snowflake                  | TV exposure linked with digital behavior.                                     | NBCU-specific hub, requires brand participation.                    | [17†L681-L689] |
| Marketing Mix Modeling (MMM)      | Channel contribution from aggregate data, privacy-safe.                       | No user-level data, requires statistical robustness.                 | [27†L265-L273] |



Reference: 
https://www.reddit.com/r/programmatic/comments/1j5q681/what_the_heck_do_i_need_a_cleanroom_for/#:~:text=%E2%80%A2%20%205mo%20ago
https://www.tredence.com/blog/a-practical-guide-for-building-marketing-measurement-in-clean-rooms#:~:text=Clean%20rooms%20provide%20the%20most,privacy%20constraints%20make%20implementation%20complex
https://www.adexchanger.com/data-exchanges/a-clean-room-that-works-with-and-across-clouds-call-it-snowflakes-chance-in-hell/
https://www.infosum.com/blog/your-data-clean-room-cant-have-skin-in-the-game#:~:text=A%20genuinely%20independent%20data%20clean,into%20a%20single%20provider%E2%80%99s%20framework
https://liveramp.com/our-platform/clean-rooms/#:~:text=Unify%20collaboration%20across%20partners%20and,Media%20Intelligence
https://www.infosum.com/blog/your-data-clean-room-cant-have-skin-in-the-game#:~:text=Second%2C%20media%20lock,could%20optimize%20their%20media%20strategy
https://www.didomi.io/blog/data-clean-rooms#:~:text=However%2C%20multi,carry%20out%20such%20complex%20activities
https://tealium.com/blog/data-strategy/sweeping-away-third-party-cookies-with-data-clean-rooms/#:~:text=There%20Are%20Two%20Kinds%20of,Data%20Clean%20Rooms
https://tinuiti.com/blog/privacy-prep/appsflyer-data-clean-room-qa/
https://www.infosum.com/blog/data-clean-rooms-are-paying-high-dividends-for-finserv-companies#:~:text=TSB%20Bank%20and%20Global%20used,and%20Save%20accounts%20by%2031




ERD:
1) Executive Summary

We propose a privacy-safe Clean Room Hub that unifies journey insights across Google/YouTube, Meta, and additional partners, overcoming walled-garden silos. The hub will ingest aggregated, policy-compliant outputs from platform clean rooms and combine them with our first-party (1P) data via identity resolution with consent controls, enabling multi-touch attribution (MTA), incrementality testing, and MMM reconciliation.

Decision to approve: Phase P0 (foundation) scope, architecture, and vendor selection path.

2) Problem Statement & Context

Current state uses last-touch attribution, misrepresenting channel influence.

Platforms provide aggregated but siloed clean-room data; no single view of cross-platform journeys.

FinTech compliance (GDPR/CCPA/GLBA) mandates privacy-safe joins, consent gating, auditability.

Objective: Deliver a governed environment to stitch exposures → clicks → conversions across platforms—without exposing PII—so we can allocate spend, optimize creative/frequency, and scale high-ROI audiences responsibly.

3) Goals / Non-Goals

Goals

Cross-platform measurement (MTA + incrementality), MMM reconciliation.

Identity resolution with hashed identifiers and consent enforcement.

Strict privacy controls (k-anonymity thresholds, differential privacy budgets, query audit).

Interoperability with top walled gardens; vendor-neutral hub.

Non-Goals

No export of any platform raw user-level data.

No direct activation of non-consented IDs.

Not replacing CDP or ad-serving stack (will integrate).

4) Requirements
4.1 Functional

Ingest aggregated outputs from Google ADH, Meta, others (hourly/daily).

Normalize to fact_impression / fact_click / fact_conversion schemas.

Identity bridge linking 1P hashed IDs ↔ platform-compatible IDs (deterministic preferred).

MTA models (position-based, time-decay, Shapley) & incrementality frameworks (geo/cell).

MMM import + reconciliation dashboard (channel contribution vs. MTA).

API/SQL interface for governed analytics; export only aggregated cohorts.

4.2 Non-Functional

Security: least privilege, column/row policies, KMS-backed key rotation.

Privacy: min cohort size (e.g., ≥50), ε-budget per analysis, full query audit.

Reliability: ≥99.9% data availability for daily jobs; recovery < 4h.

Latency: P0 daily; P1 hourly for priority channels.

Cost: <$X/day P0 infra; <$Y/month vendor fees (budget guardrails).

4.3 Compliance

GDPR/CCPA consent gating; data minimization & purpose limitation.

GLBA (as applicable): safeguarded customer information; retention ≤ policy.

5) Stakeholders & RACI
Role	Name/Team	Responsibilities	R	A	C	I
Product Owner	Marketing Analytics Lead	Roadmap & Prioritization	R	A	C	I
Tech Lead	AdTech Eng	Architecture, delivery	R		C	I
Privacy	Privacy/Legal	Policy, DPIA, DPA reviews		A	R	I
Security	Sec Eng	Controls, threat model	R		C	I
Data Eng	Growth DE	Pipelines, models	R		C	I
Finance	FP&A	Cost tracking			C	I

(R=Responsible, A=Approver, C=Consulted, I=Informed)

6) Architecture Overview

Pattern: Hub-and-Spoke Clean Room

Spokes: Platform clean rooms (Google ADH, Meta, …) → export aggregated, privacy-compliant tables.

Hub: Neutral clean room / data collaboration layer (LiveRamp / InfoSum / Snowflake / Habu).

Warehouse/Lake: Governed storage of normalized facts/dims + secure views.

Analytics: MTA, incrementality, MMM reconciliation; metric registry.

Activation: Cohort exports (thresholded) → ad platforms/CDP.

(Attach the PNG ER diagram from earlier to this section or in Appendices.)

Key flows (P0):

1P data → hash/salt → dim_customer, dim_identity, consent_event.

Platform CR exports → land → fact_impression, fact_click, fact_conversion.

bridge_identity_customer links identities to customers with link_confidence.

Privacy-safe analytics via secure views (k-anon, DP) + query_audit.

7) Data Model (Summary)

Dimensions: dim_customer, dim_identity, dim_platform, dim_campaign, dim_creative.

Facts: fact_impression, fact_click, fact_conversion (attributes JSON for partner-specific fields).

Controls: consent_event, bridge_identity_customer, query_audit, dp_noise_budget.

(Full DDL attached in Appendices.)

8) Identity & Consent

Deterministic first (hashed email/phone ↔ account).

bridge_identity_customer.link_confidence and method capture merge provenance.

Consent gating at join time; deny queries when status != granted or purpose mismatch.

9) Interoperability Strategy

Start with Google ADH + Meta.

Use vendor hub (LiveRamp/InfoSum/Snowflake/Habu) to coordinate joins and enforce governance.

For platforms lacking connectors, ingest aggregated exports and conform to internal schemas.

No user-level egress; only aggregated cohorts pass thresholds.

10) Measurement & Modeling

MTA: position-based, time-decay, Shapley; window config per channel.

Incrementality: geo/cell tests; store design & results for reproducibility.

MMM: weekly aggregates; reconcile with MTA and flag divergences in dashboards.

11) Security & Privacy Controls

Access: RBAC + ABAC (purpose-bound roles).

Data protection: KMS, HSM for salts/peppers, column-level encryption (where supported).

Governance: query_audit (analyst, purpose, thresholds, timestamp).

Privacy: k-anon ≥ 50; DP epsilon/delta managed in dp_noise_budget.

12) Data Contracts & Retention

Per-partner contract: allowed fields, refresh cadence, retention, suppression rules.

Retention: impressions 180d; conversions 24m (example; align with Legal).

Deletion: subject requests propagate to all linked identities.

13) Alternatives Considered (Build vs Buy)
Option	Pros	Cons	Est. Cost	Fit
LiveRamp	Strong ID graph (RampID), many walled-garden integrations	External dependency; licensing	$$	High
InfoSum	No data movement paradigm; strong privacy posture	Requires partner participation	$$	High
Snowflake Native	Cloud-agnostic; scales with our stack	More DIY integration work	$	Medium-High
Habu	Orchestration across multiple clean rooms	Still gated by each platform’s policies	$$	Medium-High
In-house only	Full control	Hard to achieve partner interop; slower	$	Low

Recommendation: Proceed with Snowflake + Habu or LiveRamp (run quick PoC bake-off P0).

14) Capacity, SLOs & Cost

Volume (assumption): 10–50M impressions/day across channels; clicks 1–5%; conv 0.1–1%.

SLOs: Daily pipelines by 09:00 local; P1 hourly for priority channels by P1.

Cost guardrails: Infra <$X/day P0; vendor <$Y/month. Quarterly FinOps review.

15) Risks & Mitigations

Platform policy changes → Use abstraction layer + contracts; multi-vendor connectors.

Identity drift → Confidence scoring, periodic re-merges, backtesting.

Privacy budget abuse → DP budget ledger + automated refusal for over-querying.

Attribution bias → Maintain MMM + incrementality as “truth anchors.”

16) Rollout Plan

P0 (4–6 wks)

Choose hub vendor; land ADH + Meta aggregates; build core dims/facts; enable secure views; pathing + first MTA.

P1 (6–10 wks)

Add 2–4 more platforms; hourly refresh for priority; launch incrementality framework; dashboards.

P2 (ongoing)

MMM reconciliation; automated spend reallocation recommendations; activation pipelines with thresholding.

17) Observability & QA

Data quality: freshness, completeness, FK checks; platform total reconciliations (±2–5%).

Model QA: A/B guardrails; backtests vs. business outcomes.

Monitoring: pipeline SLOs, cost alerts, DP budget alerts, access anomaly detection.

18) Open Questions

Final vendor selection (Snowflake+Habu vs. LiveRamp vs. InfoSum).

Cohort threshold policy (≥50/100?) and epsilon default.

Retention per table by regulation and business needs.

Priority order for additional platforms (e.g., Amazon/TikTok/CTV).





Architecture Design

1) High-Level Pattern (Hub-and-Spoke)

Spokes: Platform clean rooms (Google ADH, Meta, YouTube/others) export aggregated datasets on a schedule.

Hub: A neutral clean room / collaboration layer (e.g., LiveRamp, InfoSum, Snowflake, Habu) where cross-platform joins and analysis occur under privacy rules.

Core services: Identity & consent, privacy guard (k-anon + DP), query/audit, modeling compute.

Store: Warehouse/lake with curated models and secure views.

Serve: Dashboards + thresholded cohort exports for activation.

(See downloadable diagram.)

2) Component Breakdown
2.1 Ingestion & Landing

Schedulers: EventBridge/Airflow/Cloud Composer for timed pulls from each clean room.

Connectors: Serverless functions or managed connectors to fetch CSV/Parquet/BigQuery extracts.

Landing Zone: Object storage (S3/GCS) with partitioning (date/platform), checksums, immutability, encryption.

2.2 Normalization & Quality

Transform: Spark/Databricks/Glue + dbt to conform to:

fact_impression, fact_click, fact_conversion

dim_platform, dim_campaign, dim_creative

Data Quality: Great Expectations/Deequ; schema-drift alerts; reconciliation vs platform totals.

2.3 Identity Graph & Consent

Bridge: bridge_identity_customer (deterministic > probabilistic), link_confidence, method.

Consent: consent_event table gates joins; requests propagate to linked identities.

2.4 Privacy Guard & Governance

K-anonymity: Enforce minimum cohort size (e.g., ≥50) via secure views.

Differential Privacy: Noise budgets tracked in dp_noise_budget (ε/δ) with refusal when exhausted.

Query Gateway: Tokenized, purpose-bound access; query_audit logs analyst, threshold, timestamp.

Catalog: Central schema registry; data contracts per partner.

2.5 Neutral Clean Room (Hub)

Role: Interoperable collaboration and (optionally) federated analysis coordination.

Flow: Platform aggregates ↔ Hub ↔ warehouse secure views.

Exports: Only aggregated/thresholded results leave the hub.

2.6 Analytics & Serving

Modeling Compute:

MTA (position, time-decay, Shapley), configurable windows.

Incrementality (geo/cell; holdouts).

MMM reconciliation (weekly aggregates).

Serving: Dashboards/Notebooks; cohort exports (with k-anon/DP applied); API endpoints for partner uploads.

3) Data Flow (E2E)

Pull aggregated artifacts from Google ADH, Meta, YouTube (per data contracts).

Land raw extracts to object storage (immutable, encrypted).

Normalize to facts/dims; run DQ checks and reconciliations.

Link identities to customers (deterministic first); check consent at join time.

Publish privacy-safe secure views (k-anon + DP).

Analyze in neutral hub & warehouse (MTA, incrementality, MMM).

Serve dashboards and export thresholded cohorts for activation.

4) Reference Deployments
4.1 AWS-First (serverless-lean)

Landing/Store: S3 (+ Lake Formation, Glacier for archive)

Compute: Glue/EMR Serverless or Databricks on EKS; dbt on ECS/Fargate

Orchestration: EventBridge + Step Functions (or MWAA/Airflow)

ID/Consent/Policy: DynamoDB (consent ledger), API Gateway + Lambda, Secrets Manager, KMS

Governance: Lake Formation row/col policies; CloudTrail/CloudWatch logs

Hub: Snowflake on AWS / LiveRamp / Habu / InfoSum via PrivateLink or VPC peering

4.2 GCP Mapping

Landing/Store: GCS + BigQuery

Compute: Dataflow/Dataproc; dbt Cloud/Composer

Security: DLP API, CMEK, IAM Conditions

Hub: Snowflake on GCP / LiveRamp / Habu

4.3 Open-Source Option

Lakehouse: Apache Iceberg/Delta + MinIO/S3

SQL: Trino/Presto

Quality: Great Expectations

Privacy: OpenDP noise functions; custom k-anon views

5) Privacy-Safe Access (examples)

K-anonymity secure view (pseudo-SQL):

CREATE VIEW v_conv_by_channel_privsafe AS
SELECT channel, campaign_id, COUNT(*) AS convs, SUM(value) AS revenue
FROM fact_conversion
GROUP BY channel, campaign_id
HAVING COUNT(*) >= 50; -- cohort threshold


Differential privacy UDF hook (pseudo-SQL):

SELECT channel,
       dp_add_noise(SUM(value), epsilon => 0.5, delta => 1e-5) AS noisy_revenue
FROM fact_conversion
GROUP BY channel
HAVING COUNT(*) >= 50;

6) SLOs, Capacity, Cost

Throughput: 10–50M impressions/day; 1–5% clicks; 0.1–1% conversions.

Freshness: Daily T+1 P0; hourly for priority journeys in P1.

Reliability: ≥99.9% data availability; recovery <4h.

Guardrails: Budget alerts (FinOps), storage lifecycle, per-model cost tracking.

7) Observability & QA

Pipeline: Freshness/volume/FK checks; platform reconciliation (±2–5%).

Security: Access anomaly alerts; DP budget ledger monitoring.

Models: Backtests, placebo tests for incrementality, MTA stability checks.

8) Implementation Backlog (P0 → P1)

P0 (4–6 wks)

Select hub vendor; sign data contracts with Google/Meta.

Build landing → normalize → facts/dims; identity bridge; consent checks.

Publish secure views; first MTA + pathing dashboard.

P1 (6–10 wks)

Add 2–4 platforms; hourly refresh for key channels.

Stand up incrementality framework; MMM import & reconciliation view.

Cohort export APIs with threshold enforcement.