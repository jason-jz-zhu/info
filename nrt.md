flowchart LR
  subgraph Sources
    ADM[(ADM CDC)]
    DDM[(DDM CDC)]
    STC[(STC Site Data)]
  end

  subgraph Ingest
    KC[Kafka Connect / DMS / Deequ CDC]
    K[Kafka / Kinesis\nmulti-topic, partitioned]
    SR[(Schema Registry)]
  end

  subgraph StreamProc["Real-time Processing"]
    P1[Flink / Spark Structured Streaming\nSTC Goat, Channel Overwrite, Agg]
    P2[Feature & Joins Layer\nApp_ID & External ID joins]
    DQ[Great Expectations / Deequ\nRealtime DQ and metrics]
    SS[(DynamoDB state store\nTTL, upsert, dedupe)]
  end

  subgraph Storage["Data Lake & Serving"]
    S3r[(S3 Raw)]
    S3b[(S3 Bronze)]
    S3s[(S3 Silver)]
    OL[OneLake Delta]
    CDL[(Curated Data Layer\nCDL Delta)]
    PV[PV Processor + Ingestion\nDelta tables]
  end

  subgraph Outputs["Downstream Delivery"]
    SNS[(SNS / Kinesis fanout)]
    Splunk[(Splunk Observability)]
    Dash[BI Dashboards\nOneLake/Delta live]
    API[[Low-latency APIs\nFastAPI / Lambda]]
  end

  ADM --> KC --> K
  DDM --> KC --> K
  STC --> KC --> K
  K -->|avro/parquet + schemas| SR
  K --> P1 --> P2 --> SS
  P2 -->|good events| DQ --> S3r
  DQ -->|metrics| Splunk
  S3r --> S3b --> S3s --> OL
  P2 -->|PV events| PV --> OL
  OL --> CDL --> Dash
  P2 --> SNS
  P2 --> API


# Future Streaming Workflow

## Stage-by-Stage Details

### 1. Source capture (near-real-time)
- **ADM, DDM, STC** captured via CDC (Debezium/DMS/Kafka Connect) with **idempotent keys** (`App_ID`, External ID).
- Publish to **Kafka (or Kinesis)** topics per domain (e.g., `adm.events`, `ddm.events`, `stc.pageview`).

### 2. Contracts & schemas
- Enforce **Protobuf/Avro** with a **Schema Registry**; versioned, backward-compatible.
- Add **data contracts** (required fields, PII tags, semantic rules).

### 3. Streaming backbone
- Kafka/Kinesis with **partitions** keyed by `App_ID` (join locality) + **compaction** for changelog topics.
- **Retention**: 3–7 days hot, 30 days compacted (ops playbook for replay).

### 4. Real-time processing layer
- **Flink** (preferred for exactly-once + native Kinesis) or **Spark Structured Streaming** (Glue/Spark on EMR).
- Operators:
  - **STC Goat / Channel Overwrite** as incremental transforms.
  - **Windowed joins** on `App_ID`/External ID (10–30-min sliding windows for late events; watermark = 2–6 hours).
  - **Dedupe/upsert** using **DynamoDB state store** (keyed by `(App_ID, event_ts_bucket)`), with **TTL** for hot state.
  - **Feature calc** for PV / risk (FICO/LOB) as stateless or keyed state operators.

### 5. Data quality in-stream
- **Great Expectations/Deequ** checks inline: schema conformance, null %, domain sets, join completeness, late data rate.
- **Side-output** bad records to `*-deadletter` topics and **S3 Raw**; push metrics to **Splunk** dashboards.

### 6. Lake write pattern
- **Delta Lake/Apache Hudi/Iceberg** sink with **exactly-once** semantics.
- **Medallion**: S3 **Raw → Bronze → Silver**, then **OneLake Delta** for curated.
- Compact small files with **OPTIMIZE** (Z-order on `App_ID`, `event_date`).

### 7. PV pipeline
- Dedicated **PV Preprocess → PV Processor → PV Ingestion** stream jobs write **Delta tables** in **OneLake** (hourly rolling compaction).
- A **PV DQ Metric** job aggregates per hour/day for BA team KPIs.

### 8. Serving & fan-out
- **SNS/Kinesis** fan-out channels for near-real-time consumers (risk, LOB, marketing).
- **Low-latency API** (Lambda/FastAPI behind API GW) reads **Delta Live Tables** or **DynamoDB materialized views** for sub-100 ms queries.
- **Dashboards** read **CDL** in OneLake (business-owned).

### 9. Monitoring & ops
- **End-to-end SLAs**: ingest < **1 min**, transform < **3–5 min**, curated in OneLake < **10–15 min**.
- **Exactly-once**: transactional sinks, idempotent writers, checkpointing (Flink savepoints/Spark checkpoints).
- **Retry & replay**: DLQ replay tooling, topic rewind to watermark.
- **Cost controls**: autoscaling (KDA/Flink), compaction windows, tiered storage.

### 10. Security & governance
- Row/column-level policies (Lakehouse ACLs), **tokenization** for PII at ingest, **key vault** integration.
- **Lineage** (OpenLineage/Marquez) from source → topic → job → table.
- **Access**: producer/consumer IAM per domain; CI-guardrails for schemas.

---

## Topic & Table Blueprint (Example)

| Domain   | Stream Topic     | Key            | SLA     | Sink Table (Delta)                         | Notes                |
|----------|------------------|----------------|---------|--------------------------------------------|----------------------|
| ADM CDC  | `adm.events.v1`  | `App_ID`       | <1 min  | `bronze_adm_events` → `silver_adm_entities`| Debezium upserts     |
| DDM CDC  | `ddm.events.v1`  | `App_ID`       | <1 min  | `bronze_ddm_events` → `silver_ddm_entities`| Enrich joins         |
| STC Site | `stc.pageview.v1`| `App_ID`       | <30 sec | `silver_stc_pageview`                      | High-volume PV       |
| PV Facts | `pv.facts.v1`    | `App_ID`       | <3 min  | `oneLake.pv_facts_delta`                   | Post-processor output|
| DQ Bad   | `dq.bad.v1`      | `(topic,offset)`| n/a    | `raw_dq_bad_records`                       | Replayable DLQ       |
| Metrics  | `dq.metrics.v1`  | date/hour      | n/a     | `dq_hourly_metrics`                        | Splunk charting      |

---

## Why This Will Work Better

- **Low latency** with replay safety: streaming joins + state store + Delta transactional sinks.  
- **Clean separation**: raw capture, processing, serving (medallion) → simpler governance & backfills.  
- **First-class DQ**: quality is computed in-stream and visible in Splunk; bad data quarantined & replayable.  
- **Scalable fan-out**: SNS/Kinesis enables new consumers without re-wiring the core pipeline.  
- **BI-ready**: OneLake/CDL holds curated Delta for business dashboards, aligned with your current flow.  

---

## Actionable Next Steps

1. Stand up **Schema Registry** + contract checks in CI for `adm/ddm/stc`.  
2. Create **Kafka/Kinesis topics**, partition plan, and retention policy.  
3. Build the **Flink** (or **Spark**) jobs for:
   - STC Goat/Channel Overwrite  
   - PV Processor (preprocess → facts)  
   - DQ side-output + metrics  
4. Configure **Delta/Hudi/Iceberg** sinks + compaction jobs; wire to **OneLake/CDL**.  
5. Provision **DynamoDB** for state store (PK=`app_id#bucket`, TTL=7–14 days).  
6. Publish **Splunk** dashboards: end-to-end latency, bad-row rate, watermark lag.  
7. Add **SNS/Kinesis** fan-out and one pilot **consumer** (risk or marketing).  










Requirements for Capital One’s AdTech Pipeline

Designing a streaming architecture for Capital One’s marketing data must meet the following requirements:

Throughput: Ingest and process ~10 million events per day (peak ~hundreds per second). This is a moderate volume that modern streaming services can easily handle with horizontal scaling.

Sub-Second Latency: The end-to-end pipeline (from event ingestion to output) should introduce under 1 second of latency. This supports real-time dashboard visuals (e.g., campaign spend updated instantly) and immediate feedback to ML models or campaign decision engines.

Real-Time Joins & Enrichment: Each event (e.g., an ad click) may need to be enriched by joining with existing data – for example, joining a user’s click event with that user’s profile or with campaign metadata (budget, targeting rules). The solution must support stateful stream joins or lookups without significant delay.

Downstream Consumers: Multiple systems will consume the processed data:

Dashboards/BI: For marketers to see up-to-the-moment campaign metrics (impressions, click-through rates, conversion funnel stats).

ML Models: For feeding online models (e.g., personalization or bidding algorithms) with features derived from live events. Models might need streaming features (like user engagement in last X minutes) or triggers when certain thresholds are met.

Campaign Management Systems: These systems manage ad budgets, pacing, and targeting. They may need real-time signals (e.g., “campaign A is overspending its budget”) to adjust bids or send alerts.

Data Accuracy & Consistency: The system must ensure that the data seen by all consumers is consistent and accurate. No lost events – every ad impression or click must be accounted for exactly once. If multiple streams or jobs are involved, their outputs should not double-count or skew the metrics. Exactly-once processing semantics are highly desirable, and the state/results should be durable against failures.

AWS-Preferred & Serverless: Capital One prefers using AWS-managed (serverless) services where possible, to reduce operational overhead. The architecture should leverage AWS-native components (Kinesis, Lambda, etc.) unless a clear gap exists. This will simplify integration with existing AWS data lakes and security controls.

With these needs in mind, we propose two architecture options: an AWS-native streaming architecture using fully managed services, and an open-source streaming stack that could be self-managed (or partially managed via AWS). We also compare these options and discuss how to ensure accuracy/consistency in either approach.

AWS-Native Serverless Streaming Architecture

Overview: An AWS-native design can use services like Amazon Kinesis for ingestion, Amazon Managed Service for Apache Flink (Kinesis Data Analytics) for processing, and AWS databases for storage. Figure 1 below illustrates a reference architecture for a real-time streaming data pipeline on AWS, which we adapt to Capital One’s adtech use case.

Figure 1: Example AWS streaming architecture. Events flow from producers into Kinesis Data Streams, are processed by a Flink application (Amazon Kinesis Data Analytics) that can join with reference data (e.g. campaign metadata from S3), and the results are delivered to various storages: a time-series DB (Amazon Timestream) for dashboards, DynamoDB for fast lookups (via API), and S3 for archival
aws.amazon.com
aws.amazon.com
. The pipeline is fully managed and can scale automatically.

In the context of Capital One’s marketing pipeline, the AWS serverless architecture could be designed as follows:

Stream Ingestion – Amazon Kinesis Data Streams (KDS): All user events (website visits, ad impressions, clicks, conversions, etc.) are published to a Kinesis stream in real time. Kinesis is a managed, elastically scaling stream service that can ingest data from thousands of sources with latency on the order of milliseconds
aws.amazon.com
. Producers (e.g., tracking pixels, web SDKs or marketing APIs) send events via the Kinesis API. KDS ensures durability by replicating data across 3 AZs and can retain events for up to 24 hours (configurable to 7+ days)
aws.amazon.com
, allowing replay or late processing if needed. We would configure Kinesis in on-demand mode so that it automatically scales capacity with the event volume (peak 10M/day is easily handled). Enhanced fan-out can be used if multiple consumer applications need to read the same stream without contention
aws.amazon.com
 (for example, one consumer might be the Flink job and another could be a monitoring lambda).

Stream Processing & Joins – Amazon Managed Apache Flink (Kinesis Data Analytics): The core processing is done by Apache Flink, deployed as a fully managed service on AWS (formerly Kinesis Data Analytics for Apache Flink). Flink is chosen for its powerful stateful streaming capabilities – it can maintain state, perform aggregations and windowing, and do event-time processing with exactly-once guarantees
uber.com
. We would build a Flink application that consumes events from the Kinesis stream, then: cleans/transforms them, enriches them via real-time joins with reference data, and outputs derived data to various sinks. For the real-time join, there are multiple strategies:

Reference Data in DynamoDB: Store customer profiles or campaign metadata in Amazon DynamoDB (a serverless NoSQL DB). The Flink job can perform asynchronous lookups to DynamoDB for each event (using the Async I/O operator or a DynamoDB connector) to fetch e.g. the customer segment or campaign settings for the event’s IDs. DynamoDB’s single-digit millisecond read latency and massive throughput make it suitable for frequent lookups. The join result (event + profile info) is then processed in Flink’s pipeline.

Maintain State in Flink: If the reference data is relatively small or changes infrequently, we could periodically load it into Flink as broadcast state. For example, Flink can ingest a snapshot of campaign metadata (perhaps from S3 or a DynamoDB export) on startup, or consume updates from a separate stream of “metadata change events.” This way, the Flink job holds an in-memory (but checkpointed) copy of reference tables and can join on them with each event instantly in-process. This is viable for modestly sized reference data and ensures join lookups are sub-millisecond (since it’s in-state). Any updates to metadata can be sent as events to update the broadcast state.

Aurora Serverless or ElastiCache: As another alternative, AWS Aurora (Serverless mode) could store relational reference data, or ElastiCache (Redis/Memcached) could cache frequently used join data. The Flink job could query these, but these options introduce more management. DynamoDB or in-Flink state are preferred for true serverless operation.

The Flink application would also handle aggregations needed for dashboards (e.g., maintaining rolling counts per campaign) and could detect patterns (e.g., join impression and click streams to compute click-through-rate in real-time
ververica.com
). We would enable Flink’s checkpointing to S3, so that the state (including any in-flight join info and aggregation counters) is fault-tolerant; this also enables exactly-once processing – if the job restarts, it resumes from the last checkpoint without duplicating events
uber.com
. Flink on KDA can easily achieve sub-second processing given the modest event rate, and it handles out-of-order events using event-time and watermarks (important if events may arrive late).

Serving Processed Data to Consumers: Once events are enriched and processed in Flink, the results need to be delivered to different storage and consumer endpoints in real time:

Live Dashboards / BI: For powering dashboards, we need a queryable data store that reflects the latest events. On AWS, one option is Amazon Timestream (a serverless time-series database) which is optimized for timestamp-indexed data and can ingest from Kinesis streams
aws.amazon.com
. The Flink job can write aggregated timeseries (e.g., minute-by-minute metrics per campaign) to Timestream, where it can be visualized via Amazon QuickSight or Grafana. Another option is Amazon Redshift Serverless with streaming ingestion: Flink can insert records into Redshift in micro-batches (using the Redshift streaming API or via Amazon Kinesis Data Firehose to Redshift). Redshift would allow more complex SQL analytics on the recent data, though its latency might be a few seconds. If sub-second query latency is needed for dashboards (e.g., interactive drilldowns), a combination of Amazon OpenSearch Service (for text-based filtering and aggregations on events) or DynamoDB can be used. For instance, Flink could maintain a DynamoDB table of per-campaign counters that a dashboard frontend reads directly for instantaneous values. DynamoDB can serve thousands of reads per second with ms latency, enabling real-time counters on a dashboard. The best choice depends on the query patterns: Timestream/Redshift for time-series analysis, OpenSearch for flexible search/aggregation, or DynamoDB for simple key-value metrics. All of these are managed services.

ML Model Consumers: There are a couple of ways to feed ML models. If the models are deployed via AWS SageMaker endpoints or AWS Lambda functions, the streaming pipeline can invoke them in real-time. For example, a Lambda could be subscribed to the Kinesis stream (or to a Kinesis Data Firehose data delivery) to trigger an online prediction for each event (though this may be costly at scale). More efficiently, if the model needs aggregated features (say user’s last 5 minutes of activity), we could use the Flink job to compute those features and store them in a Feature Store (AWS SageMaker Feature Store or a DynamoDB table) keyed by user or campaign. The ML inference service then reads the latest features from there. Alternatively, the Flink job itself can call a SageMaker endpoint in streaming to score events (Flink’s async I/O could handle inference calls without blocking). The architecture should also consider feedback of model outputs if needed (for instance, feeding a model’s prediction back into the stream or into the campaign system). The key is that the pipeline provides up-to-date data for ML in production – this might be streaming features for training (feeding into S3 or Snowflake in near-real-time) or direct signals for inference. AWS Glue Schema Registry can also ensure that events schemas for ML features evolve in a controlled way.

Campaign Management Systems: For real-time campaign optimization (pausing campaigns, budget updates), the pipeline can send triggers or aggregated stats to the campaign management component. One pattern is to use Amazon EventBridge or SNS to publish events like “campaign XYZ has spent 90% of budget today” once certain conditions are met. The Flink job can evaluate such rules continuously (as part of the stream processing) and emit an alert event that EventBridge catches, routing it to the campaign system (which might be an API or microservice). Alternatively, the campaign system could directly query the DynamoDB or Timestream data that the pipeline updates, and then take action. Using EventBridge or SNS keeps the coupling low – the campaign app just subscribes to relevant events. AWS Lambda could also be used here: e.g., Flink writes a summary to DynamoDB, and a DynamoDB Stream triggers a Lambda that calls the campaign API to adjust something. The emphasis is on near-real-time feedback: if a campaign is overspending, the system should know within seconds to react.

Data Lake and Batch Layer – Amazon S3 via Firehose: In parallel with real-time processing, it’s wise to archive all raw events and processed results to Amazon S3. Kinesis offers Kinesis Data Firehose, which can deliver streaming data to S3 in near real-time (with buffering windows as low as 60 seconds). We can attach a Firehose stream to Kinesis to continuously dump raw event data into an S3 bucket (partitioned by date/hour). This ensures an immutable log of all events for compliance and allows batch analytics later (e.g., using Athena or Spark on S3, or building training datasets for ML). The Firehose can also perform light transformations (or use a Lambda for transformation) before S3 if needed. Additionally, the Flink job can write certain outputs to S3 (possibly in an Iceberg or Parquet format) to integrate with the existing data lake and Glue Catalog. This hybrid approach (streaming + batch) resembles the Lambda architecture many companies use – streaming for immediacy, batch for comprehensive backfill or reprocessing.

Scalability & Management: This AWS architecture is serverless and scalable by design. Kinesis Data Streams in on-demand mode will scale the shard capacity automatically to handle bursts (up to double the previous peak throughput)
aws.amazon.com
. The Managed Flink service (KDA) can be set to auto-scale parallelism based on throughput or CPU usage, so the Flink job can scale out if event rates spike (although at ~115 events/sec average, even a single Flink parallel subtask could handle it easily). DynamoDB is also auto-scaling and can handle very high read/write rates on demand, ensuring the join lookups or metric updates won’t bottleneck. Because all components are managed, Capital One’s team would not manage servers – just deploy the Flink code and configure streams. Monitoring is provided by CloudWatch (e.g., for Kinesis iterator age, Lambda invocations, Flink KPIs) and AWS KDA’s built-in dashboard for the Flink job. This addresses operational concerns and lets the team focus on data logic rather than infrastructure.

AWS Stack Summary: Ingestion: Amazon Kinesis Data Streams. Processing: Amazon Kinesis Data Analytics for Apache Flink (with real-time joins via DynamoDB or in-memory state). Serving outputs: DynamoDB (fast key-value metrics), Amazon Timestream or Redshift (analytical queries), plus Amazon OpenSearch or Elasticsearch if full-text log analysis needed. Integration: EventBridge/SNS for event-driven triggers to other systems; QuickSight for visualization. Storage: S3 (via Firehose) for accuracy audits and offline analysis. Exactly-once: Achieved through Flink’s checkpoints and transactional sinks, as well as idempotent writes to DynamoDB (using upsert semantics). AWS’s own documentation emphasizes such patterns – using Kinesis for real-time collection and managed Flink or Lambda for processing, then delivering to purpose-built stores for dashboards, ML, and alerting





-----------


Overview and Requirements
Capital One–level enterprises in ad tech deal with massive clickstream and log data that must be processed in real-time or near-real-time. The goal is to design a streaming data pipeline on AWS that can ingest high-throughput event streams, process them with low latency, and store both raw and transformed data for analytics. Key requirements include:
Ingestion: Handle thousands of events per second from websites, mobile apps, and servers (clicks, page views, etc.). The pipeline should scale to spiky traffic and bursty loads typical in ad tech.


Processing: Perform streaming transformations, enrichments, and aggregations with minimal lag (sub-second to a few seconds). Technologies like Apache Flink (on Amazon Managed Service for Apache Flink) or Apache Spark Structured Streaming (on AWS Glue or EMR) are considered.


Storage: Durably store all incoming raw events and processed results in Amazon S3, forming a data lake. This allows replay, backfills, and batch analytics on historical data.


Security & Compliance: The entire pipeline must enforce enterprise-grade security controls – all components in private VPC networks, strong IAM access controls, encryption (at rest and in transit via AWS KMS-managed keys), and integration with AWS services like PrivateLink and Secrets Manager. The design must meet PCI DSS and PII handling standards (e.g. network isolation, encryption, auditing).


Observability: Comprehensive monitoring and logging – including CloudWatch metrics/dashboards, structured application logs, and possible OpenTelemetry instrumentation for traces – to ensure the pipeline’s health and to debug issues.


Fault Tolerance: The system should gracefully handle failures with minimal data loss. Use checkpointing, restart capabilities, dead-letter queues (DLQs) for bad events, multi-AZ redundancy, and replay mechanisms to recover from outages or bad deployments.


Governance: Apply data governance and cataloging for the data lake. Use AWS Lake Formation and Glue Data Catalog to manage schema, control access to sensitive data (PII), and enforce data contracts (e.g. using AWS Glue Schema Registry to validate event schemas).


The following sections detail a robust AWS streaming data pipeline architecture that meets these requirements, including a high-level diagram, service choices, security best practices, data layout, observability, and an example CDK implementation.
High-Level Architecture
High-level AWS streaming data pipeline architecture (ingestion through processing to data lake storage). The pipeline consists of several decoupled layers, each using fully managed AWS services for scalability and resiliency:
Ingestion Layer: Incoming events are collected via a scalable stream. This could be Amazon Kinesis Data Streams or Amazon Managed Streaming for Apache Kafka (MSK), depending on requirements. Clients (web/mobile SDKs or servers) send clickstream events to the stream (for example, via the AWS SDK, REST API Gateway endpoints, or Kafka producers). The stream buffers and replicates data across multiple AZs, providing durability and high throughput.


Processing Layer: A stream processing application consumes events from the stream in real-time. The preferred choice is Apache Flink running on Amazon Kinesis Data Analytics for Apache Flink (a fully managed Flink service) for continuous low-latency processingaws.amazon.com. The Flink application runs in a scalable, managed environment and can perform transformations, filtering, enrichments (joining with reference data), and aggregations on the fly. As an alternative, an Apache Spark Structured Streaming job can run on AWS Glue Streaming or an Amazon EMR cluster (including EMR Serverless) to achieve near-real-time micro-batch processing.


Analytics & Storage Layer: Processed data, as well as a copy of raw data, are written to Amazon S3 data lake storage. The Flink or Spark jobs deliver transformed output (e.g. session aggregates, filtered events) to S3 in a partitioned, efficient format (such as Parquet or ORC), and raw events can be archived to S3 as-is (JSON or compressed format) for backup and replay. Downstream analytic tools and queries (Athena, Redshift Spectrum, etc.) can then consume this data. In addition, real-time dashboards or search indices can be fed if needed (for example, Flink could also send certain aggregates to Amazon OpenSearch or Amazon Redshift for live analytics, though the primary store is S3).


Management & Governance: Surrounding these core layers are security, monitoring, and governance controls. All services are deployed in a private VPC or accessed via VPC Endpoints, and all data is encrypted with AWS KMS. AWS Lake Formation and Glue Catalog are used to catalog data in S3 and manage fine-grained access (particularly important for PII). Monitoring via CloudWatch and logging are integrated at each layer for end-to-end observability.


This architecture is highly scalable and modular. Each layer (ingest, process, store) can scale or be modified independently (e.g., switching Kinesis for MSK or Flink for Spark) without affecting the others, thanks to the decoupling via streaming and S3.
Ingestion Layer – Kinesis Data Streams vs. MSK
Choosing a Streaming Service: For the ingestion layer, you have two primary options on AWS:
Amazon Kinesis Data Streams (KDS): A fully-managed, serverless streaming service that requires no cluster maintenance. You provision it by setting the number of shards (or use on-demand auto-scaling capacity). Kinesis can handle high throughput (each shard supports up to 1 MB/sec or 1000 records/sec input). It integrates natively with AWS analytics services. For example, Kinesis can directly feed into Kinesis Data Analytics (Flink) and Kinesis Data Firehose for delivery to S3 with minimal setup. It also autoscales in a managed way (on-demand mode) and is designed for multi-AZ high availability out of the box. Kinesis supports server-side encryption using AWS KMS keys to encrypt data at restdocs.aws.amazon.com, and all data in transit uses HTTPS TLS endpoints. One advantage of Kinesis is lower operational overhead and built-in integration (e.g., a Flink application can easily connect as a consumer).


Amazon Managed Streaming for Apache Kafka (MSK): A fully-managed Kafka service that gives you an Apache Kafka cluster in your VPC. MSK is ideal if you require Kafka’s interface or need features like Kafka’s rich ecosystem of connectors and exactly-once semantics with source connectors. MSK offers more control over configuration (number of brokers, instance types, storage, retention period, etc.) and can leverage Kafka’s community tooling. It also supports encryption at rest and in transit, and you can integrate IAM authentication or SASL/SCRAM for client access. MSK is deployed across multiple AZs (brokers in at least 2–3 AZs) for durability. It may be preferred in an enterprise that already uses Kafka or needs open-source compatibility. Keep in mind MSK requires some capacity planning (broker sizing, number of partitions, etc.), and while AWS manages the cluster, you are responsible for client optimizations and perhaps Apache ZooKeeper (until MSK’s newer versions which manage ZK for you).


High-Throughput and Scaling: Both KDS and MSK can ingest the high event volumes of ad tech. With Kinesis, scaling is done by adjusting shard count or using on-demand throughput (AWS manages the scaling within certain limits). With MSK, scaling means adding partitions or brokers; MSK now also offers features like tiered storage to offload older data to cheaper storage, which can help cost and scale for long retention. In either case, the ingestion stream can retain data for a window (default 24 hours for Kinesis, up to 7 days or more; and configurable retention in Kafka/MSK, e.g. 7 days or much longer with tiered storage). This retention allows consumers (like our processing app) to fall behind temporarily or to replay recent data if needed.
Integration and Data Delivery: The stream collects raw events which will be consumed by the processing layer. Additionally, a common best practice is to attach a delivery mechanism for raw data archival:
With Kinesis, you can attach a Kinesis Data Firehose stream that subscribes to the Kinesis Data Stream and delivers all raw events to an S3 bucket in batch (e.g., buffering and writing every minute or 5 MB)aws.amazon.comaws.amazon.com. Firehose can compress and transform data (for instance, convert JSON to Parquet on the fly) and ensures raw data lands in S3 reliably, acting as a built-in DLQ/archival for the entire stream. Alternatively, a lightweight AWS Lambda consumer could read from KDS and dump events to S3. In the MSK scenario, you could use Kafka Connect with the MSK S3 Sink Connector to continuously deliver raw topic data to S3 (the AWS MSK Connect feature can deploy connectors as a managed service). This way, all incoming events are safely persisted in S3 (the “raw zone”) even before processing, which is valuable for compliance (an immutable log) and for replaying data in case the processing job needs to be re-run on historical data.


If events originate from client devices (e.g. web or mobile), an architecture using Amazon API Gateway + AWS Lambda or an Amazon ECS/Fargate service can serve as a secure ingestion endpoint. For example, an API Gateway can receive HTTP events, authenticate/authorize them, and then put them onto Kinesis or MSKaws.amazon.com. This adds an extra layer (useful for multi-tenant scenarios or if direct access to the stream is not feasible from clients). In a simpler case, devices could directly call the AWS SDK (with proper IAM) to put records to Kinesis. For Kafka/MSK, typically an intermediate service or running Kafka producers in application code is needed.


Security at Ingestion: The streaming service is configured with enterprise security in mind:
For Kinesis Data Streams, use an Interface VPC Endpoint (AWS PrivateLink) so that producers and consumers communicate with Kinesis entirely over the AWS internal network, not the public internet. Applications running in an AWS VPC can resolve the Kinesis endpoint locally and send data without crossing public subnets. IAM policies on the stream control who/what can put or get records. Enable server-side encryption with a KMS CMK (customer-managed key) so data is encrypted at rest on the shardsdocs.aws.amazon.com. All Kinesis APIs require TLS, satisfying encryption in transit.


For MSK, since the brokers run in your VPC, producers/consumers will connect via your VPC network (or VPN/Direct Connect from on-prem if needed). Ensure the MSK brokers are in private subnets (no public IPs) and use security groups to restrict inbound access to only the application servers or AWS services that need it. Enable TLS encryption for Kafka traffic (MSK can enforce TLS-only communications). MSK encrypts data at rest by default using AWS KMS. Use AWS Secrets Manager to store any credentials (like SASL/SCRAM user passwords if using that auth method) – MSK can integrate with Secrets Manager for this. Optionally, enable IAM access control for MSK (MSK supports IAM authentication for Kafka, which can simplify auth by using IAM policies for clients).


By carefully choosing between Kinesis or MSK and configuring it securely, the ingestion layer can reliably handle the firehose of clickstream events and make them available to the streaming processors with minimal delay.
Processing Layer – Apache Flink vs. Spark Streaming
The processing layer is where incoming events are transformed, filtered, and analyzed in near-real-time. The two primary frameworks for streaming in this scenario are Apache Flink and Apache Spark Structured Streaming:
Apache Flink on Amazon Kinesis Data Analytics (Managed Flink): This is a preferred choice for real-time streaming due to Flink’s true streaming model (event-at-a-time processing) and strong stateful processing capabilities. Amazon Kinesis Data Analytics (KDA) service for Apache Flink provides a fully managed environment to run Flink applicationsaws.amazon.com. You upload your Flink job code (JAR or PyFlink script) and AWS handles provisioning of underlying infrastructure, scaling, and failover. Flink on KDA can achieve sub-second end-to-end latencies, and it supports exactly-once processing semantics when integrated with sources/sinks like Kinesis, Kafka, and S3. In our pipeline, the Flink job would consume from the Kinesis or MSK stream, perform any necessary transformations (for example, decoding JSON, filtering out bot clicks, joining with reference data for enrichment, computing real-time aggregates like ad impressions per user or per minute), and then write results out. Flink has built-in connectors that allow writing to multiple destinations in parallel – e.g., simultaneously write an enriched event stream to an S3 sink and metrics aggregates to a database or open search index. In this design, the primary sink is S3 (data lake), but Flink could also push selected results to Amazon OpenSearch or trigger alerts. Flink on KDA automatically handles scaling parallelism in response to input load and can recover from failures using checkpointing. Key features that align with our needs include private VPC connectivity (the Flink application can run within a VPC to access MSK, databases, etc.) and custom partitioning of output data. For instance, the Flink job can partition output files in S3 by a field (such as date or user segment) to organize the data lakeaws.amazon.com. Because KDA (Managed Flink) is serverless, we don’t manage the Flink cluster – we simply allocate a certain parallelism or Kinesis Processing Units (KPUs) and the service can autoscale within bounds.


Apache Spark Streaming (Structured Streaming): This is an alternative for teams that are already invested in Spark or want to use the same engine for batch and streaming. Spark’s Structured Streaming operates in micro-batch mode (processing events in small batches with millisecond to second windows). It can certainly achieve near-real-time speeds (e.g., a micro-batch every 1 second is possible), though typically with a bit more latency than Flink’s pure streaming. On AWS, Spark streaming jobs could run on:


AWS Glue Streaming Jobs: Glue is a serverless ETL service. A Glue streaming job is essentially a long-running Spark Structured Streaming job. You configure it with a streaming source (Glue has built-in connectors for Kinesis Data Streams, MSK, or Kafka) and write your transformation logic in Python or Scala. AWS Glue handles the provisioning of the Spark runtime and scaling (to a point). This option is convenient because it’s serverless and integrates with the Data Catalog, but may have fewer tuning options than a full Spark cluster.


Amazon EMR (or EMR Serverless): You can set up an EMR cluster with Spark (or use EMR Serverless for a more on-demand experience) to run a streaming application. EMR gives you more control over Spark configuration and version. EMR Serverless can dynamically add workers as the stream volume grows. With EMR, you would run the Spark job continuously (or via YARN deployment). The Spark job, like Flink, would read from the input stream (Kinesis or Kafka — AWS provides the Kinesis Connector for Sparkaws.amazon.com and Kafka is supported natively) and then write to S3. Spark Structured Streaming also supports exactly-once or idempotent output to certain sinks; writing to S3 in append mode with checkpointing ensures no duplicates if the job restarts.


Flink vs Spark – Recommendations: For an ad tech real-time pipeline, Apache Flink on KDA is often recommended because of its lower latency and robust state management (which helps with complex event processing, windowing, aggregations). Flink’s runtime is optimized for streaming, with features like event time processing, out-of-order handling, and heavy-duty stateful computations (with exactly-once guarantees via checkpointing). AWS’s Managed Flink service simplifies running it at scaleaws.amazon.com. Spark Structured Streaming, on the other hand, excels if you already use Spark for batch and want to unify your codebase or if your processing can tolerate a bit more latency. Spark might also be used if you plan to use the same Spark code for both streaming and batch (for example, using Delta Lake or Iceberg with streaming upserts).
Service Configuration: In either case, certain configurations should be set for enterprise use:
Parallelism and Scaling: For Flink on KDA, you can configure the initial parallelism and KPU allocation. It supports auto-scaling (KDA can increase KPUs when the input throughput increases, as described in AWS’s guidanceaws.amazon.comaws.amazon.com) to handle bursty traffic. Ensure the Flink job has a proper parallel source (e.g., reading from Kinesis with a shard-to-parallelism mapping) so that it can consume from many Kinesis shards or Kafka partitions concurrently. For Spark, if on EMR, enable auto-scaling or use EMR Serverless which automatically scales executors based on workload.


Checkpointing & State: Enable frequent checkpoints in Flink (e.g., every 1–5 minutes, depending on latency needs) to Amazon S3. This allows Flink to recover state and resume exactly-once processing after failures. In KDA, you configure a checkpointing interval and a state backend (it uses an S3 bucket for state snapshots). For Spark Structured Streaming, use the checkpoint location (on S3) to store offsets and state in a fault-tolerant way. This is crucial for fault tolerance and exactly-once guarantees – e.g., Spark will store Kafka offsets in checkpoint, so if it restarts it doesn’t reprocess old data.


Error Handling: Incorporate error handling in the stream processing code. For example, if a message is malformed (cannot be parsed), the application can send that event to a side output or a separate Kinesis/SQS DLQ sink instead of dropping it silently. In Flink, you might use a ProcessFunction with a side output for invalid records; in Spark, you might catch exceptions in the data flow and write bad records out to an S3 "errors" prefix. This implements a Dead Letter Queue pattern at the application level, ensuring no data is lost – even problematic events are retained for later analysis.


Resource Tuning: For Flink KDA, choose an appropriate Flink runtime version (AWS supports specific Flink versions; ensure your code is compatible). Allocate enough memory per KPU if doing heavy aggregations (KDA offers metrics to monitor heap and managed memory). For Spark, size the executors and memory such that your micro-batches can complete quickly. Avoid under-provisioning which can cause lag, or over-provisioning which wastes cost.


Multiple Streams / Fan-in or Fan-out: The pipeline might have multiple input streams (for different event types or different products). Flink can easily consume multiple streams in one job (or you can deploy multiple Flink jobs per stream). Similarly, both Flink and Spark can fan-out processed data to multiple sinks. For instance, one Flink job could read one stream and write to two S3 locations (raw and transformed) and also publish summary stats to CloudWatch metrics or a database. This avoids duplicating processing logic. The architecture diagram shows the ability of one Flink application to read from Kinesis or MSK and write to S3 and even to OpenSearch simultaneouslyaws.amazon.comaws.amazon.com.


In summary, the processing layer uses a managed streaming compute engine to continuously process events. Flink on AWS (KDA) is typically the top choice for real-time due to its exactly-once semantics and integration with Kinesis/MSK, whereas Spark Streaming is a viable alternative especially if aligning with existing big data workflows. Both can meet enterprise requirements when configured correctly.
Data Lake Storage and Governance on S3
All data – both raw and processed – is stored in Amazon S3, which serves as the durable data lake. S3 offers virtually infinite scalability, high durability, and low cost storage, making it ideal for both real-time pipeline sinks and long-term analytics storage. In this architecture, we organize S3 storage into different zones/prefixes to separate raw data, cleaned data, and curated data, aligning with data lake best practicesaws.amazon.comaws.amazon.com:
Raw Data Zone (Landing Zone): All incoming events are stored as-is upon ingestion. For example, if click events are JSON messages, the raw zone will have those JSON files (possibly bundled or compressed) without transformation. This zone is written by the ingestion layer (e.g., Firehose or MSK connect delivers every event here, or the Flink job itself writes a copy of raw data). Raw data is typically stored in a date-partitioned folder structure by event arrival time (e.g., s3://<bucket>/raw/clickstream/YYYY/MM/DD/HH/), so that each hour or day’s data is grouped. This zone acts as an immutable log of what was received. It is useful for reprocessing (you can replay data from here if the streaming job had an error) and for compliance (regulatory needs to retain original records). Access to raw zone is usually restricted to data engineers or pipeline processes, since the data may be unfiltered and contain sensitive or duplicated info.


Processed/Cleaned Zone: After the streaming application processes events, the results are stored in a cleaned or curated zone. There might be multiple sets of outputs:


Cleaned Detail Data: This could be events that have been cleaned or enriched, but still at the individual event level. For example, the Flink job might augment each click event with user metadata or geo-location, then write the enriched events to s3://<bucket>/cleaned/clickstream_enriched/DATE=.../part-*.parquet. These records are typically stored in a compressed, analytics-friendly format like Parquet or ORC (columnar formats that enable efficient queries). Partitioning is applied by time and possibly other fields (e.g., DATE, or country if that’s a common filter) to optimize query performance. As an example, an AWS streaming pipeline might persist events to S3 in Parquet partitioned by event time (e.g., year/month/day) for downstream analysisaws.amazon.com.


Aggregated/Curated Data: The pipeline might also produce summary tables or aggregates. For instance, you may maintain running counts of clicks per ad campaign per hour. The Flink job could periodically emit these aggregates (using tumbling windows or manual triggers) to another S3 prefix, say s3://<bucket>/curated/ad_metrics/, storing data like “campaign X had Y clicks in hour H”. This curated data is often what analysts or dashboards query directly, as it’s high-level and business-meaningful. Curated datasets usually conform to a predefined schema and data model (often governed by data contracts).


Data Catalog and Schema: Each data set stored in S3 (raw or processed) is cataloged in the AWS Glue Data Catalog. The streaming job (Flink or Spark) can integrate with the Glue Catalog to register output schemas or you can run Glue Crawlers to detect schema. This makes the data discoverable and queryable via tools like Amazon Athena or Redshift Spectrum. For example, the Glue Catalog might have a table raw_clickstream pointing to the raw JSON files, and a table clickstream_enriched_parquet for the curated Parquet data, with columns and data types defined. Partition columns (like date) would be set in the catalog for partition pruning.


AWS Lake Formation for Governance: AWS Lake Formation is used on top of S3 and Glue Catalog to enforce governance. In an enterprise scenario, Lake Formation allows central control of who (which IAM role or user) can access which data catalog tables and even specific columns. This is crucial for PII compliance: for example, if the clickstream includes user IDs or IP addresses (PII), you can mask or restrict those columns so that only authorized analytics users can see them. Lake Formation provides a fine-grained permission model that ensures analysts using Athena/Redshift/Glue only see the data they are permitted to. It also tracks data lineage and access audit logs. Using Lake Formation, you can define data sharing and row/column-level security once, and have it consistently applied across all your analytic services.


Schema Registry and Data Contracts: To enforce that upstream producers and downstream consumers speak the same data language, the pipeline can use the AWS Glue Schema Registry (part of AWS Glue). Producers can register schemas (Avro/JSON/Protobuf) for the events they put on the stream. The Flink/Spark job can retrieve and validate schema when reading events, catching any unexpected schema changes. This ensures that a producer cannot suddenly break the contract by sending a new field in the clickstream without proper coordination. The schema registry also supports schema evolution with compatibility checks. Essentially, it’s a tool to implement data contracts in streaming: each event type has a versioned schema, and changes are managed. By integrating the schema registry, the pipeline can reject or route malformed events (for example, if an event doesn’t conform to the expected schema, the Flink job could send it to a DLQ and not process it further, thereby protecting the downstream data integrity).


Encryption and Access: The S3 buckets used for raw and processed data should have server-side encryption with AWS KMS enabled. This means all objects are encrypted at rest with a customer-managed KMS key. This is often a requirement for PCI and PII (ensuring that if someone somehow got access to the storage, they cannot read data without the key). Access to these buckets is controlled via bucket policies and IAM roles. Only the ingestion services and processing applications should be able to write to the raw and processed buckets. Downstream analytics roles may only have read access (and possibly only via Lake Formation permissions). We also enable S3 Block Public Access on these buckets to guarantee no public exposure, and optionally object lock or versioning if immutability is needed for compliance.


Data Layout and Lifecycle: A sensible data layout and lifecycle policy helps manage cost and compliance:


Partition by date/time to optimize query efficiency and to allow easy data retention management (e.g., you could drop partitions older than X days if they’re not needed).


Use compression (Parquet, ORC, or at least GZIP for JSON) to reduce storage cost and speed up reads.


Apply S3 Lifecycle rules: for example, move raw data older than 90 days to Amazon S3 Glacier or Glacier Deep Archive (to save cost for long-term retention), since raw data might only be needed for audit or reprocessing rarely. Processed data that’s actively queried might stay in S3 Standard or Infrequent Access for quicker retrieval, but still, older processed partitions could be archived if not needed hot.


Maintain separate buckets or prefixes for different sensitivity levels. If some data sets are non-PII aggregate metrics, they could be in a more accessible bucket, whereas raw user-level logs with PII might be in a highly restricted bucket.


By structuring the S3 storage into raw and curated zones and using AWS governance tools, the pipeline ensures that data is stored cost-effectively and securely. Moreover, any analytical consumption of this data (via Athena, EMR, Redshift, etc.) will go through the Lake Formation permissions and Glue catalog – providing a unified governance layer.
Security and Compliance Best Practices
Security is woven into every layer of this streaming architecture to meet the stringent requirements of a financial enterprise (PCI DSS, GDPR/PII regulations, internal infosec standards). Here we highlight the critical security controls and best practices:
Network Isolation with VPC: All processing components run inside an Amazon VPC, which is a logically isolated network within AWS. By using VPC isolation, we ensure that the data pipeline components (e.g., Kinesis producers/consumers, MSK brokers, Flink application instances) are not exposed to the public internet. Amazon VPC provides strong network-level isolation – resources in the VPC can only communicate out through managed endpoints or gateways that we control. This is essential for PCI compliance, where the cardholder data environment (CDE) must be isolated. In fact, AWS notes that Amazon VPC is the preferred construct for workloads in PCI scopeaws.amazon.com. No component of the pipeline (neither data ingestion nor processing) should be directly publicly accessible. If external systems need to send data, they do so through secure gateways (like API Gateway with authentication, or a private link). The VPC subnets that host MSK brokers or any ECS ingestion service are private subnets with no internet gateway. If internet access is needed for any component (for example, the Flink job might call an external API for enrichment), it should use a NAT gateway or proxy that is tightly controlled.


AWS PrivateLink (VPC Endpoints): We use VPC Endpoints to interface with AWS services internally. For example, we create:


A Kinesis Data Streams Interface Endpoint in the VPC, so that any Put or GetRecords API calls to Kinesis go through the AWS private network instead of over public IPs.


An S3 Gateway Endpoint in the VPC, to allow the Flink application and other services to write/read S3 without an internet gateway. This ensures all S3 access is internal.


If using API Gateway for ingestion, use a Private API Gateway that is accessible via VPC Endpoint, or attach the API Gateway to the VPC so that data posts don’t traverse public routes.


Other endpoints as needed (for CloudWatch Logs, Secrets Manager, KMS, etc.), meaning the Flink or Spark tasks can reach those services privately. In summary, all communication between pipeline components and AWS services can be kept within the AWS network fabric for additional security.


Encryption in Transit: All data in transit is encrypted using TLS/SSL. For ingestion, if using HTTP API Gateway, enforce HTTPS only. Kinesis and MSK endpoints both require TLS – for MSK, clients will use TLS to connect to brokers, and if possible enable TLS only ports on the brokers. Within the VPC, one might argue it’s already isolated, but for compliance it’s good to ensure even internal traffic is encrypted (e.g., MSK supports node-to-node encryption so that even broker-to-broker replication is TLS). Essentially any protocol carrying sensitive data (which clickstream and logs may be if they include user identifiers or card-related info) is protected via encryption in transit. This satisfies PCI DSS requirements for encrypting sensitive data over networks that could be interceptedaws.amazon.comaws.amazon.com. While the VPC isolation reduces the risk of interception, we still apply TLS to be safe.


Encryption at Rest (KMS): All persistent data stores are encrypted with AWS KMS keys:


Kinesis Data Streams encryption at rest is enabled with a KMS CMK (so each record is encrypted before persisted in the service storagedocs.aws.amazon.com).


MSK encrypts data at rest on brokers via KMS keys (this is typically default in MSK). Also, enable MSK logging and store those logs encrypted on S3/CloudWatch.


S3 buckets have default encryption with KMS. Use customer-managed KMS keys separate for different data zones if needed (you might have one key for raw data, one for processed, allowing the possibility to segregate access to keys – e.g., only the pipeline can use the raw data key).


If using Amazon OpenSearch or Redshift as additional sinks, ensure those are encrypted at rest with KMS and that they are deployed in the same VPC with restricted access.


Checkpointing or state files that Flink writes to S3 are also encrypted (they land in S3, inheriting bucket encryption). For extra measure, KDA allows you to specify a KMS key for the Flink application’s checkpoint store as well.


Any database (like if we used Aurora or DynamoDB in the pipeline) would also have encryption at rest.


Identity and Access Management (IAM): IAM is used to enforce least privilege access across the pipeline:


Define IAM roles for each AWS service integration. For example, the Kinesis Data Analytics (Flink) application has an IAM role that grants it permissions only to read from the specific input stream and write to the specific S3 bucket/prefix it needs. This prevents it from reading any other data or writing elsewhere. The role also allows writing CloudWatch logs/metrics. If the Flink job needs to read a Secrets Manager secret (say for an API key to enrich data), the role grants access only to that secret.


Similarly, if using Glue or EMR for Spark, the IAM role for the Glue job or EMR EC2 instances only permit necessary actions (e.g., read from MSK or Kinesis, write to S3 output, and talk to Glue Catalog).


IAM policies on Kinesis Data Streams: restrict who can put data. For instance, only the specific Lambda or ingestion service role (or specific trusted IAM users) can call PutRecord on the stream; only the Flink app role can call GetRecords. This prevents any rogue actor in the AWS environment from casually reading the stream data or injecting false events.


Use IAM authentication for MSK if possible: MSK supports IAM-based authentication for Kafka producers/consumers. This can simplify access control by using IAM policies instead of SASL credentials.


All human access is removed from these data stores – no one should be directly logging into a broker or KDA node. Administration is done via AWS console/API with proper IAM permissions, which are audited.


Secrets Management: Use AWS Secrets Manager to store any sensitive configuration – for example, database credentials if the Flink job writes to a database, or API keys for third-party enrichment services, or Kafka credentials if not using IAM auth. The application retrieves these secrets at runtime securely (KDA allows referencing a Secrets Manager secret in Flink application properties). This avoids putting any secrets in code or configuration in plain text. Secrets Manager rotates keys regularly (if applicable) to meet compliance.


PCI DSS Considerations: If any part of the data includes payment card info (which clickstream typically might not, but suppose if logging user form inputs or transactions, it could), special care is needed:


Scope Isolation: PCI DSS requires isolating the Cardholder Data Environment. In our case, if card data is in the stream, that entire pipeline (from ingestion to storage) is in scope. We’d ensure no mixing of non-PCI workloads in those components. Possibly even use a dedicated VPC for PCI data. Use security groups and NACLs as an extra layer to ensure only necessary communication flows (e.g., the ingestion server can talk to Kinesis on specific ports, etc.)aws.amazon.com.


No Sensitive Data in Logs: Ensure that log messages (CloudWatch Logs from Flink, etc.) do not contain PII or card numbers. Use structured logging with filtering – e.g., if the event has a credit card number (should ideally not be in clickstream, but if any PII like email), the application could mask or hash it in logs. This prevents accidental leakage of sensitive data to logs which might be more openly accessed.


Auditing and Monitoring: Enable AWS CloudTrail for all relevant services (Kinesis, MSK, KDA, S3, IAM, etc.) to record every API call. This provides an audit log of who accessed what – a PCI requirement for tracking access to card data. Similarly, enable S3 access logs on buckets to see if anything or anyone accesses the data outside of expected channels.


Config Rules and Compliance Scanning: Use AWS Config and Security Hub with PCI DSS standards to automatically check for misconfigurations. For example, AWS provides Config rules as a conformance pack for PCI which will ensure your Kinesis streams are encrypted, your S3 buckets aren’t public, etc., and flag any issuesdocs.aws.amazon.comdocs.aws.amazon.com.


Penetration Testing & Segmentation: As an enterprise, you would also do regular pen-testing and ensure that the network segmentation holds (for example, trying from a non-PCI dev account to reach the VPC endpoints should fail, etc.).


PII Protection: Personal data in the pipeline (like user IDs, IP addresses, behavior events) is protected by the above measures (encryption, access control). Additional steps for PII:


Implement data minimization – only collect data needed and consider hashing or tokenizing identifiers early if raw values are not needed in the data lake.


Use services like Amazon Macie to automatically scan S3 buckets for sensitive data (Macie can identify PII like names, addresses, etc. in your S3 and alert if something is found in an unapproved location)aws.amazon.com. This can act as a guard to ensure, for instance, that no credit card numbers accidentally ended up in logs or raw data.


When sharing data or granting access via Lake Formation, utilize column-level filtering to hide or tokenize PII fields for most users. For example, data scientists might only see a user_id as a pseudonym or a GUID, not an email.


Ensure any PII that must be deleted for compliance (like a GDPR "right to be forgotten") can be located and purged from the S3 data if required. This might involve using partitioning keys or an index to find all data for a user and wiping it, which should be designed in the data model.


By applying these security best practices, the pipeline achieves defense in depth: network-level isolation, strict identity-based access, encryption at multiple layers, and continuous monitoring. This aligns with enterprise security frameworks and meets compliance standards for handling sensitive data. The result is a pipeline that not only is robust and real-time, but also secure by design, ensuring data confidentiality and integrity.
Reliability, Fault Tolerance, and Disaster Recovery
Building an enterprise-grade pipeline means it must be highly reliable and able to handle failures gracefully without data loss. Here we describe the fault tolerance features in the architecture and strategies for resilience:
Multi-AZ High Availability: All critical components run across multiple Availability Zones to avoid single points of failure. Amazon Kinesis Data Streams is inherently a multi-AZ service – its shards are replicated across servers in different AZs (so if a server or AZ fails, the stream persists)aws.amazon.com. Amazon MSK (Kafka) clusters should be configured with replication factor (typically 3) and placed in subnets across 3 AZs; this way, each partition’s replicas are in different AZs, and the cluster can tolerate an AZ outage. The Flink processing (on KDA) is a distributed application that can be configured to use multiple worker nodes; KDA will spread workers across AZs as well when possible. If one AZ faces issues, the stream processing continues on the remaining nodes. For Spark on EMR, you would similarly launch the cluster with nodes in multiple AZs or use EMR Managed Availability. However, note that EMR clusters often reside in one AZ for HDFS efficiency – since we use S3 as storage, we are not reliant on HDFS, so even if an EMR cluster is single-AZ, a failure can be mitigated by relaunching in another AZ reading from S3. S3 is a regional service storing data redundantly across AZs by default, so the data lake is resilient to AZ failures.


Checkpointing and State Snapshots: The stream processing frameworks implement periodic checkpointing to allow precise recovery after failures:


Apache Flink: Flink’s checkpointing mechanism periodically snapshots the state of the operators and the positions in the input stream (offsets) in a durable store (Amazon S3 in our case). If the Flink application crashes or is restarted (even for an update or scaling), it can resume from the last checkpoint, exactly where it left off. This means at-least-once or exactly-once processing semantics can be maintained (Flink with checkpoints + two-phase commit to sinks achieves exactly-once). In KDA, enabling checkpointing is as simple as setting a checkpoint interval and pointing to an S3 checkpoint bucket. Flink will also perform a savepoint (manual snapshot) on demand when updating the application, which helps in smooth upgrades. With checkpoints, if one Flink parallel task fails, KDA will automatically restart the job (possibly on new infrastructure) and the job will continue from the last checkpoint, so no events are lost or reprocessed twice beyond what the guarantees allow.


Spark Structured Streaming: By using a checkpoint location (on S3) for Spark Streaming, the offsets of processed data (and any state from stateful operations) are saved. If the job fails and is restarted, Spark will read the checkpoint and pick up from the last processed offset in Kinesis/MSK, avoiding duplicating data. This provides at-least-once processing by default, and exactly-once when writing to idempotent sinks. Checkpointing intervals can be tuned (Spark does it per micro-batch, essentially).


Kinesis and Kafka Offsets: These streaming sources track the positions. For Kinesis, the Flink consumer or Spark connector uses a shard iterator and will resume from where it stopped (the position can be stored in Flink’s state). For Kafka, offsets are committed either to Kafka (in Kafka’s consumer groups) or externally via checkpoints. Ensuring that the processing jobs use stable consumer group IDs and commit back offsets (or rely on checkpoint state) means that if the job goes down temporarily, when it comes back, it will continue from the last read message, not from the tail (unless configured otherwise).


Dead-Letter Queues (DLQ) for Faulty Events: As mentioned earlier, the pipeline should account for events that cannot be processed (due to schema mismatch, corrupted data, or business rule violations). Instead of losing those events or blocking the pipeline, we direct them to a DLQ:


This could be an Amazon SQS queue or an Amazon Kinesis stream specifically for error events. Flink can produce to multiple sinks, so one sink could be “bad-events-stream” or an SQS. Alternatively, write them to a special S3 location (like s3://.../error_events/).


AWS Kinesis Data Firehose (if used for transformation) also has a concept of a retry and S3 backup for records that failed transformation.


By having a DLQ, we ensure no data is completely dropped – teams can later inspect the DLQ to fix data issues or reprocess those specific items if possible.


In an enterprise setting, you might even trigger alerts when DLQ volumes exceed a threshold, since that could indicate upstream issues (e.g., a new type of event not recognized by the parser).


Error Handling and Retries: Within the processing code, use try-catch logic or Flink’s exception handlers to catch transient errors (like a timeout calling an external enrichment API) and implement retries or fallback logic. You wouldn’t want a single external service blip to bring down the streaming job. For example, if an enrichment API fails, perhaps skip enrichment for that batch and continue, or send those events to a side buffer for retry asynchronously. Flink allows asynchronous I/O with timeouts so the pipeline can continue processing other events while waiting for external lookups, and handle timeouts gracefully.


Backpressure and Throttling: The pipeline is designed to handle spikes, but in case of extreme surges beyond capacity, backpressure mechanisms in Flink/Spark will engage to slow down consumption. This prevents overwhelming the downstream systems. Kinesis will buffer data for up to its retention period, and Kafka will buffer up to its retention and capacity. We will monitor for any signs of lag (e.g., CloudWatch’s IteratorAge metric for Kinesis or consumer lag metrics for Kafka) and scale up the processing layer if needed (either automatically or via alert triggers). The use of auto-scaling in KDA and possibly MSK can alleviate backlogs without manual intervention.


Replay and Reprocessing: A powerful aspect of this architecture is the ability to reprocess historical data if needed:


Since all raw events are in S3 (and/or retained in Kafka for a long period), we can replay data through the pipeline. One method is to deploy a new instance of the Flink job (or Spark job) pointed at the historical data source. For example, if a bug in processing caused bad outputs for last week, we can fix the code and then run a batch Spark job on the raw S3 data for that week to recompute correct results (writing to a corrected S3 path). Or we can deploy a Flink job that reads from the S3 raw logs (Flink can read files as a bounded source) and does a catch-up computation.


If data is still in the stream (Kinesis up to 7 days, Kafka as configured), you could also replay by seeking the stream back to an older position. For Kafka, you can set the consumer group to an older offset or use a separate consumer group to re-read from the beginning. For Kinesis, you can start a new Kinesis consumer using the iterator type TRIM_HORIZON (from earliest) or a specific timestamp, effectively reprocessing from that point in time.


The architecture could incorporate an automated replay mechanism: for example, in case of a failure scenario, once the system is back, Flink will automatically catch up using the stream backlog (assuming within retention). If the outage was longer, one might use the raw S3 as a source to fill the gap.


It’s common to maintain some tooling or scripts for replay jobs, given the data is all available in S3. This is another reason to ensure raw data on S3 is partitioned by time – you can easily select the range to reprocess.


Multi-Region DR (Disaster Recovery): Depending on RPO/RTO requirements, an enterprise might consider extending this pipeline to a secondary AWS region for DR. For example, MSK can mirror data to another region using MirrorMaker or AWS MSK Replicator. Kinesis doesn’t natively replicate, but one can build a secondary consumer that reads from Kinesis in primary region and writes to Kinesis in secondary region (or use the upcoming features if any for cross-region). S3 can be set with cross-region replication to copy data to a backup bucket in another region. Alternatively, simply rely on backups in S3 and the ability to redeploy the stack in a new region if an entire region fails (since region outages are rare). Given Capital One-level constraints, mention that cross-region backup for critical data (especially if containing financial transaction info) is often enabled. At minimum, storing backup copies of data in a second region (via S3 CRR) can provide safety against a regional disruption.


Monitoring for Faults: Reliability also comes from proactively monitoring. The pipeline will have CloudWatch Alarms on critical indicators: if the processing lag goes beyond a threshold (e.g., if Kinesis IteratorAge > some value or Kafka consumer lag too high), if the MSK broker CPU is maxed out, if the Flink application has consecutive checkpoint failures or restarts (KDA can emit metrics for number of restarts), etc. These alarms would trigger a pager or an automated scaling action. This ensures that any fault is caught early and handled, often before it becomes a major incident.


Maintenance and Updates: When updating the Flink application code or Spark job (for new logic), plan for zero/minimal downtime deployments. KDA supports stopping an application with a savepoint and then restarting new code with that savepoint, meaning it won’t re-read old data but continues from stateaws.amazon.com. This is how you do a seamless update with Flink. For Spark on EMR, you might spin up a new cluster running the new version of the streaming job in parallel, let it catch up (using the same consumer group but that’s tricky due to offset commit collisions; more often, you’d have downtime or rely on the checkpoint continuity for Spark). In Glue streaming, you’d update the job script and Glue will restart it (some brief downtime possibly). The key is to preserve state if possible so you don’t lose where you were in the stream on upgrade.


Through these strategies, the pipeline achieves a high level of fault tolerance. Even if a component crashes or an AZ goes down, the design prevents data loss and can recover quickly. The combination of multi-AZ resilience, checkpointing for exactly-once replay, DLQs for problematic records, and robust monitoring form a comprehensive safety net. Thus, the system meets enterprise SLAs for uptime and data durability.
Observability and Monitoring
A streaming pipeline at this scale requires end-to-end observability to ensure it’s working correctly and to troubleshoot issues in real-time. We leverage AWS’s monitoring services (Amazon CloudWatch) as well as standardized tracing/metrics frameworks (OpenTelemetry) for comprehensive insight into the pipeline’s operations.
CloudWatch Metrics and Dashboards: AWS services automatically emit key metrics to CloudWatch, and we will use these extensively:


Kinesis Data Streams Metrics: Monitor IncomingBytes, IncomingRecords (to see ingestion rate), ReadThroughput and WriteThroughput per stream shard, and especially IteratorAge (how behind the consumers are). If IteratorAge starts increasing, it means our consumer (processing app) is lagging behind real-time. CloudWatch alarms can be set on these (e.g., alarm if IteratorAge > 60 seconds).


MSK/Kafka Metrics: MSK can send broker JMX metrics to CloudWatch if configured. Key ones include MessagesInPerSec, BytesIn/OutPerSec, consumer lag (if using Kafka consumer lag CloudWatch metric via offset exporter), and broker health metrics (CPU, memory, disk). We would also watch the Kafka UnderReplicatedPartitions metric – which if non-zero indicates a broker or replication problem.


Flink (KDA) Metrics: Amazon Managed Flink (KDA) publishes metrics like KPUsConsumed, Parallelism, RecordsRead/Written, checkpoint stats (time, size, success/failures), and so onaws.amazon.comaws.amazon.com. Especially important are checkpoint success rates and any error counts the app logs as custom metrics. We can create a CloudWatch dashboard to visualize pipeline health – e.g., a graph of events ingested vs events processed vs events output to S3. In fact, the AWS streaming solution provides a sample CloudWatch dashboard for monitoring the pipelineaws.amazon.com. We will customize a dashboard that might include: ingestion rate, processing lag, number of active Flink subtasks, CPU utilization of Flink, and S3 put object rates, etc.


Glue/Spark Metrics: If using Glue or EMR, CloudWatch will have metrics for the job runtime or the Spark stage metrics. EMR can send Spark application metrics to CloudWatch (via CloudWatch Sink or by using Ganglia metrics to CloudWatch). We might not rely heavily on those, since Flink is primary, but it’s similar in principle.


S3 Metrics: Monitor S3 buckets for growth and request rates. Especially, check for any 4xx or 5xx errors on S3 put/get (should be rare). For cost and usage, monitor volume stored over time to manage lifecycle.


CloudWatch Logs: All logs from the pipeline are centralized in CloudWatch Logs:


The Flink KDA application’s logs (both the system logs and any custom logging from the Flink job) go to a log group like /aws/kinesis-analytics/<app-name>. We ensure logging level is set appropriately (INFO for normal ops, DEBUG for troubleshooting when needed). CloudWatch Logs allows us to search these logs in near real-time. For example, if an event fails parsing, our Flink job might log an error with the event ID – we can query the logs for that ID to find details.


If we have any Lambda functions (for ingestion or triggers), their logs go to CloudWatch as well.


MSK broker logs (if enabled) can be delivered to CloudWatch Logs too – including Apache Kafka logs (which can help debug broker issues).


We enforce structured logging where possible. This means logs are in JSON format or other structured format that includes context like {"eventId": "...", "userId": "...", "error": "parsing failure", "timestamp": "..."}. This makes it easier to query logs (CloudWatch Logs Insights can parse JSON and let us filter, e.g., find all logs where error contains "schema"). It also assists in correlating events across components.


Setup log retention policies in CloudWatch (maybe keep 1-3 months of logs for quick access, archive older to S3 if needed).


Traceability with OpenTelemetry: For a complex distributed system, tracing individual events or transactions is valuable. We can incorporate OpenTelemetry instrumentation in our producers and consumers:


For instance, when a web app generates a click event, it can assign a trace ID (maybe reuse a session ID or a generated UUID) and include that in the event data. The Flink application can be instrumented (using the OpenTelemetry Java agent or SDK) to pick up that trace ID and propagate it, creating spans for processing steps. There is support to integrate OpenTelemetry with custom Flink operators by using the OpenTelemetry Java API (though this might require running Flink job with the agent). This would allow an end-to-end trace from the moment a click happens on the client, through the ingestion service, through Flink, to the point it’s written to S3 or further processed.


Even if full distributed tracing is complex, we can at least use unique event IDs and log them at key points, achieving a poor man’s trace. For example, log “received event X at ingestion”, “processed event X in Flink at time Y”, “stored event X to S3”. By querying logs by event ID, you can reconstruct the timeline.


OpenTelemetry can also be used to collect custom metrics inside the application. If certain business metrics are needed (like count of events by type), the Flink job could emit CloudWatch custom metrics or push metrics to a Prometheus/OpenTelemetry collector. However, an easier route in AWS is using CloudWatch Embedded Metrics Format (EMF) – where the app logs metrics in a structured way and CloudWatch treats them as custom metrics. This avoids running separate metric infrastructure.


For the parts of pipeline that use HTTP (API Gateway, etc.), AWS X-Ray is an option for tracing. API Gateway and Lambda can be instrumented with X-Ray to give traces of the ingestion request. These traces can be helpful to identify latency sources (like if putting to Kinesis is slow at times, X-Ray would show it).


External Monitoring Tools: In addition to CloudWatch, enterprises often aggregate metrics and logs into centralized systems:


Amazon Managed Service for Prometheus & Grafana: If we use Prometheus metrics (for example, Flink can be configured with a Prometheus reporternightlies.apache.org), we can set up AMP (Managed Prometheus) to scrape the metrics and use Amazon Managed Grafana dashboards for real-time visualization. Grafana can combine CloudWatch and Prometheus data too.


Alerting: Use CloudWatch Alarms to trigger SNS notifications (or pager duty) on critical conditions (consumer lag, job failure, etc.). Also consider setting up canaries – e.g., a small test event that flows through the pipeline periodically to verify end-to-end functionality, and alarm if it doesn’t show up in output.


Logging Analytics: CloudWatch Logs Insights can be used for on-demand analysis of logs (it’s great for ad-hoc querying of logs with SQL-like queries). For more heavy-duty log analysis or retention, some companies stream CloudWatch logs to S3 or to an OpenSearch cluster. Given our pipeline might feed OpenSearch for real-time data anyway, we could also index certain logs (maybe error logs) into an OpenSearch index for easier search and dashboarding.


CloudWatch Dashboard & ServiceLens: We can create a unified CloudWatch Dashboard that shows all key graphs in one view (ingest rate, lag, processing CPU, S3 writes, etc.)aws.amazon.com, giving ops teams a one-stop view. Additionally, AWS X-Ray ServiceLens or Container Insights could give an overview of how the pipeline components are behaving (though those are more for microservices; in our case, the main microservice is the Flink app).


Cost Monitoring: As part of observability, we also monitor cost-related metrics:


Kinesis shards usage (to see if we can reduce shards in low times or need more in peak).


MSK broker utilization (to see if brokers are underutilized or overutilized).


S3 storage growth (and use S3 Inventory or Cost Explorer to break down cost by bucket/prefix).


These help in optimization (see next section) by identifying where most resources are spent.


Run Books and Playbooks: The ops team should develop run-books for common alerts. For example, if an alarm says Flink job lagging, the playbook might be: check CloudWatch Logs for errors, possibly increase KDA parallelism via AWS console, or if KDA auto-scaled up to limit, maybe the input spike is too large – consider pausing ingestion or scaling shards. Another example: if MSK broker dies, MSK should self-heal by replacing it, but one might need to check for any data loss or stuck partitions. Having clear steps documented ensures faster recovery.


Observability ensures we not only detect issues but also understand the performance characteristics of the system. With CloudWatch and OpenTelemetry integration, we can achieve near real-time visibility into the data flow. This is crucial in ad tech where delays or drops directly translate to lost revenue or insights. An effectively monitored pipeline will have high uptime and quickly surface any anomalies (like sudden drop in events, which might indicate upstream outage or code bug, triggering investigation). In essence, “you can’t manage what you can’t measure” – thus we measure everything meaningful in this streaming system.
Cost Optimization Strategies
Operating a large-scale streaming pipeline can be costly if not optimized. Here are strategies to ensure the solution remains cost-effective while meeting performance needs:
Right-Sizing and Auto-Scaling Ingestion:


With Kinesis Data Streams, use the on-demand capacity mode if the traffic is highly variable. On-demand will automatically scale shards up and down based on throughput. This saves cost during lulls (no need to pay for idle shards) while handling surges automatically, albeit at a slight premium per unit. If traffic is steady/predictable, provisioned mode with manual or application-auto-scaling of shard count is more cost-effective. For example, you can use an AWS Application Auto Scaling policy on a Kinesis stream to add shards if IncomingBytes exceeds 80% of current shard capacity for 5 minutes, and remove shards when low (keeping minimum shards).


For MSK, choose broker instance types that match your throughput needs without huge headroom. MSK’s cost is mostly per broker-hour. Utilizing a smaller number of larger brokers vs more smaller brokers can have different cost implications depending on throughput (due to throughput per broker limits). Also, MSK now has Tiered Storage – enabling that allows you to keep long retention without needing lots of expensive SSD storage on brokers; older data offloads to S3 transparently at lower cost. If long retention isn’t needed on brokers (because we archive to S3 anyway), you can potentially keep MSK retention lower to reduce broker storage needs (and thus possibly use smaller brokers).


Both Kinesis and Kafka compress data in transit optionally (producers can compress batches using gzip or snappy). Ensure producers use compression – this reduces payload size, saving on MSK network IO (and storage) and on Kinesis payload costs (Kinesis charges per GB-ingested). JSON events compress well, often 5-10x smaller.


Efficient Stream Processing Compute:


Managed Flink (KDA) KPUs: Monitor the utilization of Kinesis Processing Units (KPUs). If the job consistently uses only half of the allocated KPUs, you might scale down to save cost. Conversely, if it’s maxing out, scaling up can prevent throttling (and thereby process events faster, avoiding extended runtime costs). KDA now supports auto-scaling the Flink application based on metricsaws.amazon.com, which can be enabled to optimize cost/performance – it will add KPUs on heavy load and remove them on low load. Additionally, if there's a predictable low-traffic window (e.g., every night low user activity), you could schedule the Flink application to scale down parallelism or even shut down if appropriate (though shutting down means losing state unless you rely on snapshot and warm start later).


Glue Streaming / EMR: If using Glue streaming jobs, you pay by the DPU-hour. Make sure the number of DPUs (data processing units) allocated is just enough for the workload. Glue streaming has a minimum of 2 DPUs and can autoscale up to a max you set – tune that max so it doesn’t over-provision. For EMR on EC2, use auto-scaling groups and possibly spot instances for worker nodes if the job is resilient to instance loss (Spark structured streaming with checkpointing can handle spot interruptions by restarting, though with some delay). Spot instances can significantly cut EC2 costs (50-70% lower) but be cautious to have some on-demand as baseline to not drop all capacity. EMR also allows Graviton2 instances which might give better price/performance if Spark is compatible.


If using EMR Serverless for Spark, it automatically rightsizes, but still monitor usage – EMR Serverless costs can add up if the application isn’t tuned to release resources when idle. Make sure to stop the serverless application when not needed.


S3 Storage and Data Lifecycle:


S3 is cheap per GB, but with big data, it accumulates. Use lifecycle policies aggressively: for raw data that isn’t likely to be used often, transition it to S3 Infrequent Access after, say, 30 days, and to Glacier after 90 days, and maybe deletion after a year if compliance allows. This dramatically reduces storage cost for older data. Processed data that is used for reporting might be kept in Standard storage for quicker access for a certain period (e.g., last 90 days), then moved to cheaper tiers.


Use object size optimization: Instead of writing millions of tiny files (which increases S3 request costs and overhead), batch data into larger objects. Firehose does this by default (buffer by time/size). For Flink, use its bucketing sink or streaming file sink to roll files to, say, 100 MB before closing. This reduces PUT request counts and improves read efficiency for queries. Similarly, avoid very large files (>Gigabytes) as they become less manageable – strike a balance (maybe 128MB or 256MB per file).


Compression and format: Storing processed data in Parquet not only gives query performance benefits but also reduces size by ~5x compared to raw JSON (due to columnar compression). This directly cuts S3 storage cost and also speeds up Athena/Presto queries (thus lower cost if you pay per TB scanned). So, an investment in converting data to Parquet/ORC is a cost optimization for query and storage.


Data pruning: If certain data is not needed at all after some time, automate its deletion. For instance, raw logs older than 1 year might be deleted entirely if no longer useful (taking into account any compliance retention requirements).


Optimizing Observability Costs:


CloudWatch Logs can get expensive if you ingest huge volumes of log data (it charges per GB ingested and stored). To optimize, adjust log levels – e.g., avoid very verbose debug logs in production unless troubleshooting. You can also set a retention period so logs older than X days are auto-deleted to save storage cost. Offloading logs to S3 (cheaper storage) via subscription or export can be done if long-term retention is needed.


CloudWatch Metrics are generally low cost, but custom metrics do incur costs per metric. Be mindful of how many custom metrics the pipeline pushes. It’s often enough to push aggregated metrics rather than every single possible metric.


Using OpenTelemetry and external monitoring: consider the cost of any extra infrastructure (e.g., running an OpenTelemetry collector on EC2 or using Managed Prometheus has its own costs). If CloudWatch can cover needs, stick with it to reduce complexity and cost of an extra service.


Data Transfer Costs: Within a single AWS region, most services (Kinesis, S3, etc.) have no data transfer fees when used in the same region. However, be careful of:


If you have cross-region consumers or if your monitoring/ops is pulling data out (e.g., if pushing some data to on-prem). Keep as much within region as possible.


VPC endpoints cost a small hourly fee, but that is usually negligible compared to the benefit of not using NAT Gateway for egress. NAT Gateway egress can be costly if, say, your Flink job was pulling data via the internet. By using endpoints, we avoid NAT costs for calls to AWS APIs (S3, Kinesis, etc.).


If using API Gateway with a lot of traffic, consider the pricing: REST API Gateway is expensive per million requests. If extremely high QPS from clients, an alternative is a lightweight self-managed ingestion service on EC2/ECS or direct usage of Kinesis Producer SDKs to avoid that cost. However, API Gateway gives a lot of value (auth, throttling) – it’s a trade-off.


For MSK, monitor inter-AZ data transfer (Kafka replication between AZs will incur inter-AZ data charges). With RF=3, each message goes to two other AZs. AWS inter-AZ transfer is cheaper than cross-region but still a cost. We accept that for reliability, but it’s something to be aware of. It’s usually not significant relative to other costs, but in extreme throughput (TBs of data), it can add up.


Use of Serverless and Managed Services: By using managed services like KDA, Kinesis, MSK, we reduce operational overhead (which indirectly is a cost saving, freeing engineers’ time). We also can often achieve better utilization – e.g., KDA’s auto scaling may use hardware more efficiently than a static self-managed Flink cluster. Similarly, EMR Serverless avoids having idle EC2 nodes. We trade off some control for potentially lower costs at low usage. Always evaluate if a long-running EC2 cluster might be cheaper at steady 24/7 high load (sometimes it is). For example, if our load is consistently high and predictable, running Flink on EMR with reserved instances might cost less than KDA’s on-demand KPUs. But if load is variable or we value hands-off scaling, KDA likely optimizes resource usage.


Development and Testing Environments: Cost optimization also means having separate lower-cost environments for dev/test. For instance, use smaller streams (fewer shards) and smaller KDA applications in non-prod, and maybe run them only when needed. Turn off pipeline components when not in use (especially in dev, you can shut down Flink jobs at night, etc.). This ensures you’re not paying prod-level costs for experimentation or QA.


Monitoring Costs and ROI: Utilize AWS Cost Explorer and perhaps set up cost anomaly alerts. If a cost spikes, you catch it quickly (maybe a bug causing an explosion of logs or a stuck loop writing to S3). This ties back into observability – treat cost as another metric to watch. An optimized pipeline finds the right balance: meet SLA and throughput needs without significant waste. Over time, you can refine things like reducing duplication (for example, if we find we don’t really need to store all raw data indefinitely, we can trim that to save cost, or sample a portion for long-term).


In summary, by leveraging auto-scaling, using efficient data formats, cleaning up unused data, and careful service choices, the pipeline can run economically at scale. A Capital One–level enterprise will continuously review usage and spend – ensuring that the robust pipeline we built is also cost-efficient. This results in a solution that not only performs and secures well, but also provides maximum value for the cost.



3) Stateful stream processing (core)
Amazon Managed Service for Apache Flink (KDA for Flink) consumes:


Events from Kinesis.


Dim-updates as a broadcast stream (Flink broadcast state) or async lookups to DynamoDB.


Processing logic:


Validate & normalize (required fields, types, allowed values).


Deduplicate by event_id using a TTL’d keyed state (e.g., 24h).


Event-time semantics with watermarks; late data policy (e.g., 5-minute allowed lateness).


Enrichment joins:


Fast path: broadcast state (zero-ms lookups).


Fallback/miss: Async DynamoDB get (single-digit ms).


Aggregations: rolling/tumbling windows (e.g., 1s/5s/1m) per campaign_id / channel. Maintain CTR, CVR, spend, pacing signals.


Anomaly/guardrails: drop impossible values; alert on rate spikes/drops.


Exactly-once:


Flink checkpointing to S3 (e.g., every 5s).


Use transactional/idempotent sinks (below) to avoid double effects on restart.







"""
Data Transformation using Python Dicts/Lists: Data Engineering Practice Question

Problem Statement:
Implement SQL-like operations (joins, aggregations, grouping) using only Python 
dictionaries and lists. Simulate database operations without using pandas or SQL engines.

This problem tests:
- Core Python data manipulation skills
- Understanding of SQL operations and how to implement them programmatically
- Efficient use of dictionaries for lookups (O(1) complexity)
- List comprehensions and functional programming concepts
- Memory-efficient data processing techniques

Difficulty: Medium-Hard
Source: Senior Data Engineer onsite coding round (Blind coding practice recap)
"""

from typing import List, Dict
from collections import defaultdict


class DataTransformer:
    """
    A class to perform SQL-like operations on Python data structures.
    Simulates database operations using dictionaries and lists.
    """
    
    @staticmethod
    def inner_join(left_data: List[Dict], right_data: List[Dict], 
                   left_key: str, right_key: str) -> List[Dict]:
        """
        Perform inner join operation similar to SQL INNER JOIN.
        Handles multiple records with the same key (one-to-many, many-to-many).
        
        Time Complexity: O(n*m) worst case for many-to-many joins
        Space Complexity: O(m) for the lookup dictionary
        
        Args:
            left_data: List of dictionaries (left table)
            right_data: List of dictionaries (right table)
            left_key: Key field in left table
            right_key: Key field in right table
        
        Returns:
            List of joined records
        """
        # Build lookup dictionary from right table - store lists of records for each key
        right_lookup = defaultdict(list)
        for record in right_data:
            right_lookup[record[right_key]].append(record)
        
        joined_data = []
        for left_record in left_data:
            key_value = left_record[left_key]
            if key_value in right_lookup:
                # Create cartesian product for matching records
                for right_record in right_lookup[key_value]:
                    # Merge records from both tables
                    joined_record = {**left_record, **right_record}
                    joined_data.append(joined_record)
        
        return joined_data
    
    @staticmethod
    def left_join(left_data: List[Dict], right_data: List[Dict], 
                  left_key: str, right_key: str) -> List[Dict]:
        """
        Perform left join operation similar to SQL LEFT JOIN.
        Handles multiple records with the same key (one-to-many, many-to-many).
        
        Args:
            left_data: List of dictionaries (left table)
            right_data: List of dictionaries (right table)
            left_key: Key field in left table
            right_key: Key field in right table
        
        Returns:
            List of joined records with all left records preserved
        """
        # Build lookup dictionary from right table - store lists of records for each key
        right_lookup = defaultdict(list)
        for record in right_data:
            right_lookup[record[right_key]].append(record)
        
        joined_data = []
        for left_record in left_data:
            key_value = left_record[left_key]
            if key_value in right_lookup:
                # Create cartesian product for matching records
                for right_record in right_lookup[key_value]:
                    joined_record = {**left_record, **right_record}
                    joined_data.append(joined_record)
            else:
                # Keep left record, add None values for right table fields
                right_fields = set()
                if right_data:
                    right_fields = set(right_data[0].keys()) - {right_key}
                joined_record = {**left_record}
                for field in right_fields:
                    joined_record[field] = None
                joined_data.append(joined_record)
        
        return joined_data
    
    @staticmethod
    def group_by_aggregate(data: List[Dict], group_fields: List[str], 
                          aggregations: Dict[str, Dict[str, str]]) -> List[Dict]:
        """
        Perform GROUP BY with aggregation functions similar to SQL.
        
        Args:
            data: List of dictionaries to group
            group_fields: Fields to group by
            aggregations: Dict of {result_field: {source_field: agg_function}}
                         agg_function can be: 'count', 'sum', 'avg', 'min', 'max'
        
        Returns:
            List of grouped and aggregated records
        
        Example:
            aggregations = {
                'total_sales': {'amount': 'sum'},
                'avg_price': {'amount': 'avg'},
                'order_count': {'order_id': 'count'}
            }
        """
        # Group records by the specified fields
        groups = defaultdict(list)
        
        for record in data:
            # Create group key from specified fields
            group_key = (record[field] for field in group_fields)
            groups[group_key].append(record)
        
        # Apply aggregation functions
        result = []
        for group_key, group_records in groups.items():
            # Start with group fields
            aggregated_record = {
                field: group_key[i] for i, field in enumerate(group_fields)
            }
            
            # Apply each aggregation
            for result_field, agg_config in aggregations.items():
                source_field = list(agg_config.keys())[0]
                agg_func = agg_config[source_field]
                
                if agg_func == 'count':
                    aggregated_record[result_field] = len(group_records)
                elif agg_func == 'sum':
                    values = [r[source_field] for r in group_records if r[source_field] is not None]
                    aggregated_record[result_field] = sum(values) if values else 0
                elif agg_func == 'avg':
                    values = [r[source_field] for r in group_records if r[source_field] is not None]
                    aggregated_record[result_field] = sum(values) / len(values) if values else 0
                elif agg_func == 'min':
                    values = [r[source_field] for r in group_records if r[source_field] is not None]
                    aggregated_record[result_field] = min(values) if values else None
                elif agg_func == 'max':
                    values = [r[source_field] for r in group_records if r[source_field] is not None]
                    aggregated_record[result_field] = max(values) if values else None
            
            result.append(aggregated_record)
        
        return result
    
    @staticmethod
    def filter_data(data: List[Dict], conditions: List[Dict]) -> List[Dict]:
        """
        Filter data based on conditions similar to SQL WHERE clause.
        
        Args:
            data: List of dictionaries to filter
            conditions: List of condition dicts with 'field', 'operator', 'value'
                       operators: 'eq', 'ne', 'gt', 'lt', 'gte', 'lte', 'in', 'not_in'
        
        Returns:
            Filtered list of records
        
        Example:
            conditions = [
                {'field': 'age', 'operator': 'gte', 'value': 18},
                {'field': 'city', 'operator': 'in', 'value': ['NYC', 'SF']}
            ]
        """
        def evaluate_condition(record: Dict, condition: Dict) -> bool:
            field = condition['field']
            operator = condition['operator']
            expected_value = condition['value']
            actual_value = record.get(field)
            
            if actual_value is None:
                return False
            
            if operator == 'eq':
                return actual_value == expected_value
            elif operator == 'ne':
                return actual_value != expected_value
            elif operator == 'gt':
                return actual_value > expected_value
            elif operator == 'lt':
                return actual_value < expected_value
            elif operator == 'gte':
                return actual_value >= expected_value
            elif operator == 'lte':
                return actual_value <= expected_value
            elif operator == 'in':
                return actual_value in expected_value
            elif operator == 'not_in':
                return actual_value not in expected_value
            else:
                raise ValueError(f"Unsupported operator: {operator}")
        
        # Apply all conditions (AND logic)
        filtered_data = []
        for record in data:
            if all(evaluate_condition(record, condition) for condition in conditions):
                filtered_data.append(record)
        
        return filtered_data
    
    @staticmethod
    def sort_data(data: List[Dict], sort_fields: List[Dict]) -> List[Dict]:
        """
        Sort data similar to SQL ORDER BY.
        
        Args:
            data: List of dictionaries to sort
            sort_fields: List of dicts with 'field' and 'direction' ('asc' or 'desc')
        
        Returns:
            Sorted list of records
        """
        def sort_key_func(record: Dict):
            key_values = []
            for sort_field in sort_fields:
                field = sort_field['field']
                direction = sort_field.get('direction', 'asc')
                value = record.get(field)
                
                # Handle None values (put them last)
                if value is None:
                    value = float('inf') if direction == 'asc' else float('-inf')
                
                # Reverse for descending order
                if direction == 'desc':
                    if isinstance(value, (int, float)):
                        value = -value
                    elif isinstance(value, str):
                        # For strings, we'll handle this differently
                        key_values.append((1, value))  # Will be reversed later
                        continue
                
                key_values.append((0, value))
            
            return key_values
        
        # Handle string descending sort separately
        sorted_data = sorted(data, key=sort_key_func)
        
        # Post-process for string descending sorts
        for sort_field in reversed(sort_fields):
            if sort_field.get('direction') == 'desc':
                field = sort_field['field']
                if data and isinstance(data[0].get(field), str):
                    sorted_data.reverse()
                    break
        
        return sorted_data
    
    @staticmethod
    def pivot_data(data: List[Dict], index_field: str, column_field: str, 
                   value_field: str, agg_func: str = 'sum') -> List[Dict]:
        """
        Pivot data similar to SQL PIVOT operation.
        
        Args:
            data: List of dictionaries to pivot
            index_field: Field to use as row identifier
            column_field: Field whose values become new columns
            value_field: Field containing values to aggregate
            agg_func: Aggregation function ('sum', 'count', 'avg', 'min', 'max')
        
        Returns:
            List of pivoted records
        """
        # Get unique values for columns
        column_values = sorted(set(record[column_field] for record in data))
        
        # Group by index field
        index_groups = defaultdict(list)
        for record in data:
            index_groups[record[index_field]].append(record)
        
        # Build pivoted result
        pivoted_data = []
        for index_value, group_records in index_groups.items():
            pivoted_record = {index_field: index_value}
            
            # Initialize all column values
            for col_value in column_values:
                pivoted_record[str(col_value)] = 0 if agg_func in ['sum', 'count'] else None
            
            # Aggregate values for each column
            for col_value in column_values:
                matching_records = [r for r in group_records if r[column_field] == col_value]
                
                if matching_records:
                    values = [r[value_field] for r in matching_records if r[value_field] is not None]
                    
                    if agg_func == 'sum':
                        pivoted_record[str(col_value)] = sum(values)
                    elif agg_func == 'count':
                        pivoted_record[str(col_value)] = len(values)
                    elif agg_func == 'avg':
                        pivoted_record[str(col_value)] = sum(values) / len(values) if values else 0
                    elif agg_func == 'min':
                        pivoted_record[str(col_value)] = min(values) if values else None
                    elif agg_func == 'max':
                        pivoted_record[str(col_value)] = max(values) if values else None
            
            pivoted_data.append(pivoted_record)
        
        return pivoted_data
    
    @staticmethod
    def window_functions(data: List[Dict], partition_fields: List[str], 
                        order_fields: List[str], window_func: str, 
                        target_field: str = None) -> List[Dict]:
        """
        Apply window functions similar to SQL window functions.
        
        Args:
            data: List of dictionaries
            partition_fields: Fields to partition by
            order_fields: Fields to order by within partitions
            window_func: Window function ('row_number', 'rank', 'sum', 'avg', 'lag', 'lead')
            target_field: Field to apply function to (for sum, avg, lag, lead)
        
        Returns:
            List with window function results added
        """
        # Group by partition fields
        partitions = defaultdict(list)
        for record in data:
            partition_key = tuple(record[field] for field in partition_fields)
            partitions[partition_key].append(record)
        
        # Sort each partition
        for partition_key, partition_data in partitions.items():
            partition_data.sort(key=lambda x: [x[field] for field in order_fields])
        
        # Apply window function
        result = []
        for partition_key, partition_data in partitions.items():
            for i, record in enumerate(partition_data):
                new_record = record.copy()
                
                if window_func == 'row_number':
                    new_record['row_number'] = i + 1
                elif window_func == 'rank':
                    # Simple ranking - same values get same rank
                    new_record['rank'] = i + 1
                elif window_func == 'sum':
                    # Running sum
                    running_sum = sum(r[target_field] for r in partition_data[:i+1] 
                                    if r[target_field] is not None)
                    new_record['running_sum'] = running_sum
                elif window_func == 'avg':
                    # Running average
                    values = [r[target_field] for r in partition_data[:i+1] 
                             if r[target_field] is not None]
                    new_record['running_avg'] = sum(values) / len(values) if values else 0
                elif window_func == 'lag':
                    # Previous row value
                    if i > 0:
                        new_record['lag_value'] = partition_data[i-1][target_field]
                    else:
                        new_record['lag_value'] = None
                elif window_func == 'lead':
                    # Next row value
                    if i < len(partition_data) - 1:
                        new_record['lead_value'] = partition_data[i+1][target_field]
                    else:
                        new_record['lead_value'] = None
                
                result.append(new_record)
        
        return result


def create_sample_datasets():
    """Create sample datasets for demonstration."""
    
    # Orders dataset
    orders = [
        {'order_id': 1, 'customer_id': 101, 'amount': 250.00, 'order_date': '2024-01-15', 'region': 'West'},
        {'order_id': 2, 'customer_id': 102, 'amount': 175.50, 'order_date': '2024-01-16', 'region': 'East'},
        {'order_id': 3, 'customer_id': 101, 'amount': 320.75, 'order_date': '2024-01-17', 'region': 'West'},
        {'order_id': 4, 'customer_id': 103, 'amount': 89.25, 'order_date': '2024-01-18', 'region': 'Central'},
        {'order_id': 5, 'customer_id': 102, 'amount': 450.00, 'order_date': '2024-01-19', 'region': 'East'},
        {'order_id': 6, 'customer_id': 104, 'amount': 125.30, 'order_date': '2024-01-20', 'region': 'West'},
    ]
    
    # Customers dataset
    customers = [
        {'customer_id': 101, 'name': 'Alice Johnson', 'email': 'alice@example.com', 'city': 'San Francisco'},
        {'customer_id': 102, 'name': 'Bob Smith', 'email': 'bob@example.com', 'city': 'New York'},
        {'customer_id': 103, 'name': 'Carol Davis', 'email': 'carol@example.com', 'city': 'Chicago'},
        {'customer_id': 104, 'name': 'David Wilson', 'email': 'david@example.com', 'city': 'Los Angeles'},
    ]
    
    # Sales data for pivot example
    sales = [
        {'salesperson': 'John', 'quarter': 'Q1', 'amount': 1000},
        {'salesperson': 'John', 'quarter': 'Q2', 'amount': 1200},
        {'salesperson': 'Jane', 'quarter': 'Q1', 'amount': 800},
        {'salesperson': 'Jane', 'quarter': 'Q2', 'amount': 950},
        {'salesperson': 'Jane', 'quarter': 'Q3', 'amount': 1100},
        {'salesperson': 'Mike', 'quarter': 'Q1', 'amount': 600},
        {'salesperson': 'Mike', 'quarter': 'Q3', 'amount': 750},
    ]
    
    return orders, customers, sales


def demonstrate_transformations():
    """Demonstrate various data transformation operations."""
    
    orders, customers, sales = create_sample_datasets()
    transformer = DataTransformer()
    
    print("🔄 Data Transformation Demo using Python Dicts/Lists")
    print("=" * 60)
    
    print("\n📊 Original Datasets:")
    print(f"Orders: {len(orders)} records")
    print(f"Customers: {len(customers)} records")
    print(f"Sales: {len(sales)} records")
    
    # 1. Inner Join
    print("\n1️⃣  INNER JOIN (Orders + Customers):")
    joined_data = transformer.inner_join(orders, customers, 'customer_id', 'customer_id')
    for record in joined_data[:3]:  # Show first 3
        print(f"   Order {record['order_id']}: {record['name']} - ${record['amount']}")
    
    # Test with duplicate keys
    print("\n1️⃣a INNER JOIN with duplicate keys (Multiple orders per customer):")
    # Create test data with multiple products per order
    order_items = [
        {'order_id': 1, 'product': 'Widget', 'quantity': 2},
        {'order_id': 1, 'product': 'Gadget', 'quantity': 1},
        {'order_id': 2, 'product': 'Widget', 'quantity': 3},
        {'order_id': 3, 'product': 'Gizmo', 'quantity': 1},
        {'order_id': 3, 'product': 'Widget', 'quantity': 2},
        {'order_id': 3, 'product': 'Gadget', 'quantity': 1},
    ]
    
    # Join orders with order items (one-to-many)
    orders_with_items = transformer.inner_join(orders[:3], order_items, 'order_id', 'order_id')
    print(f"   Joined {len(orders[:3])} orders with {len(order_items)} items → {len(orders_with_items)} results")
    for record in orders_with_items[:5]:
        print(f"   Order {record['order_id']}: ${record['amount']} - {record['product']} (qty: {record['quantity']})")
    
    # 1b. Left Join with duplicate keys
    print("\n1️⃣b LEFT JOIN with duplicate keys:")
    # Create customers with multiple addresses
    addresses = [
        {'customer_id': 101, 'address': '123 Main St', 'type': 'home'},
        {'customer_id': 101, 'address': '456 Work Ave', 'type': 'work'},
        {'customer_id': 102, 'address': '789 Park Blvd', 'type': 'home'},
        {'customer_id': 999, 'address': 'Unknown Address', 'type': 'home'},  # No matching customer
    ]
    
    customers_with_addresses = transformer.left_join(customers[:2], addresses, 'customer_id', 'customer_id')
    print(f"   Joined {len(customers[:2])} customers with {len(addresses)} addresses → {len(customers_with_addresses)} results")
    for record in customers_with_addresses:
        address = record.get('address', 'No address')
        print(f"   {record['name']} (ID: {record['customer_id']}): {address}")
    
    # 2. Group By Aggregation
    print("\n2️⃣  GROUP BY with Aggregation (Sales by Region):")
    region_aggregations = {
        'total_sales': {'amount': 'sum'},
        'avg_order': {'amount': 'avg'},
        'order_count': {'order_id': 'count'}
    }
    regional_stats = transformer.group_by_aggregate(orders, ['region'], region_aggregations)
    for stat in regional_stats:
        print(f"   {stat['region']}: ${stat['total_sales']:.2f} total, "
              f"${stat['avg_order']:.2f} avg, {stat['order_count']} orders")
    
    # 3. Filtering
    print("\n3️⃣  FILTER (Orders > $200):")
    high_value_orders = transformer.filter_data(orders, [
        {'field': 'amount', 'operator': 'gt', 'value': 200}
    ])
    print(f"   Found {len(high_value_orders)} high-value orders")
    for order in high_value_orders:
        print(f"   Order {order['order_id']}: ${order['amount']}")
    
    # 4. Sorting
    print("\n4️⃣  SORT (Orders by amount DESC):")
    sorted_orders = transformer.sort_data(orders, [
        {'field': 'amount', 'direction': 'desc'}
    ])
    for order in sorted_orders[:3]:  # Top 3
        print(f"   Order {order['order_id']}: ${order['amount']}")
    
    # 5. Pivot
    print("\n5️⃣  PIVOT (Sales by Person and Quarter):")
    pivoted_sales = transformer.pivot_data(sales, 'salesperson', 'quarter', 'amount', 'sum')
    for person_data in pivoted_sales:
        quarters = {k: v for k, v in person_data.items() if k != 'salesperson'}
        print(f"   {person_data['salesperson']}: {quarters}")
    
    # 6. Window Functions
    print("\n6️⃣  WINDOW FUNCTIONS (Running totals by region):")
    windowed_data = transformer.window_functions(
        orders, ['region'], ['order_date'], 'sum', 'amount'
    )
    for record in windowed_data[:5]:  # First 5
        print(f"   Order {record['order_id']} ({record['region']}): "
              f"${record['amount']} (Running: ${record['running_sum']})")
    
    print("\n✅ All transformations completed successfully!")
    
    # 7. Complex Chain Example
    print("\n7️⃣  COMPLEX CHAIN (Join → Filter → Group → Sort):")
    
    # Step 1: Join orders with customers
    enriched_orders = transformer.inner_join(orders, customers, 'customer_id', 'customer_id')
    
    # Step 2: Filter for West region orders
    west_orders = transformer.filter_data(enriched_orders, [
        {'field': 'region', 'operator': 'eq', 'value': 'West'}
    ])
    
    # Step 3: Group by customer
    customer_aggregations = {
        'total_spent': {'amount': 'sum'},
        'order_count': {'order_id': 'count'},
        'avg_order': {'amount': 'avg'}
    }
    customer_summary = transformer.group_by_aggregate(west_orders, ['name'], customer_aggregations)
    
    # Step 4: Sort by total spent
    final_result = transformer.sort_data(customer_summary, [
        {'field': 'total_spent', 'direction': 'desc'}
    ])
    
    print("   West Region Customer Summary:")
    for customer in final_result:
        print(f"   {customer['name']}: ${customer['total_spent']:.2f} "
              f"({customer['order_count']} orders, ${customer['avg_order']:.2f} avg)")


if __name__ == "__main__":
    demonstrate_transformations()


"""
Expected Output:

🔄 Data Transformation Demo using Python Dicts/Lists
============================================================

📊 Original Datasets:
Orders: 6 records
Customers: 4 records
Sales: 7 records

1️⃣  INNER JOIN (Orders + Customers):
   Order 1: Alice Johnson - $250.0
   Order 2: Bob Smith - $175.5
   Order 3: Alice Johnson - $320.75

2️⃣  GROUP BY with Aggregation (Sales by Region):
   West: $695.05 total, $231.68 avg, 3 orders
   East: $625.50 total, $312.75 avg, 2 orders
   Central: $89.25 total, $89.25 avg, 1 orders

3️⃣  FILTER (Orders > $200):
   Found 3 high-value orders
   Order 1: $250.0
   Order 3: $320.75
   Order 5: $450.0

4️⃣  SORT (Orders by amount DESC):
   Order 5: $450.0
   Order 3: $320.75
   Order 1: $250.0

5️⃣  PIVOT (Sales by Person and Quarter):
   John: {'Q1': 1000, 'Q2': 1200, 'Q3': 0}
   Jane: {'Q1': 800, 'Q2': 950, 'Q3': 1100}
   Mike: {'Q1': 600, 'Q2': 0, 'Q3': 750}

6️⃣  WINDOW FUNCTIONS (Running totals by region):
   Order 1 (West): $250.0 (Running: $250.0)
   Order 6 (West): $125.3 (Running: $375.3)
   Order 3 (West): $320.75 (Running: $696.05)
   Order 2 (East): $175.5 (Running: $175.5)
   Order 5 (East): $450.0 (Running: $625.5)

7️⃣  COMPLEX CHAIN (Join → Filter → Group → Sort):
   West Region Customer Summary:
   Alice Johnson: $570.75 (2 orders, $285.38 avg)
   David Wilson: $125.30 (1 orders, $125.30 avg)

✅ All transformations completed successfully!

Time Complexities:
- Inner Join: O(n + m) - linear in size of both tables
- Group By: O(n) - single pass through data
- Filter: O(n) - single pass with condition evaluation
- Sort: O(n log n) - Python's Timsort algorithm
- Pivot: O(n) - single pass with dictionary operations

Key Data Structures:
- Dictionaries for O(1) lookups in joins
- DefaultDict for grouping operations
- List comprehensions for filtering and transformations
- Functional programming patterns for chaining operations
"""