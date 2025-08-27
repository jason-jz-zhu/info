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