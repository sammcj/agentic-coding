# Your RAG Pipeline Is Lying to You. Here's What's Actually Going Wrong

Every company I talk to right now is building a RAG pipeline. Retrieval augmented generation. You take your company's documents, you chunk them up, you embed them into a vector database, and then when someone asks a question, the system retrieves relevant chunks and feeds them to a language model. It sounds like the right architecture. It is the right architecture. And almost everyone is building it wrong.

Not wrong as in it doesn't work. Wrong as in it works just well enough to be dangerous. Your RAG system returns answers. Those answers sound confident. They cite your documents. And according to research from Databricks and Patronus AI, roughly 15 to 30% of RAG responses in enterprise deployments contain what they call context-grounded hallucinations. Not hallucinated from thin air. Worse. Assembled from real fragments of your actual data into conclusions your documents never supported.

That is a fundamentally different failure mode from what most teams are testing for. Full stop. It is the one that will cost you.

## The Problem Isn't Retrieval. It's Assembly

When teams discover their RAG system is producing wrong answers, the instinct is to fix retrieval. Better embeddings. More sophisticated chunking. Reranking layers. Hybrid search combining vector and keyword approaches. And retrieval does matter. A study from Stanford's NLP group found that retrieval quality accounts for roughly 40% of downstream answer quality in RAG systems. That is significant and worth investing in.

But the other 60% is what happens after retrieval. The model receives five, ten, maybe twenty chunks of text and has to synthesise them into a coherent answer. This is where the real failures live, and almost nobody is testing for them systematically.

Think of it like a courtroom. Retrieval is the discovery phase, where lawyers collect all the relevant documents. Assembly is the closing argument, where someone has to take those documents and construct a coherent narrative. You can have perfect discovery, every relevant document in the pile, and still get a closing argument that misrepresents what the evidence actually shows. A lawyer who does that gets disbarred. Your RAG pipeline does it quietly, every single day, and nobody is checking the transcript.

I give credit where it's due. The teams building better retrieval are solving a real problem. Retrieval was genuinely bad eighteen months ago and the improvements have been meaningful. But if you stop there, you are optimising the discovery phase while nobody is watching the closing argument. And it is the closing argument your users actually see.

## The Assembly Failure Triad

I've been running evals on RAG systems across multiple domains for the past several months. Legal documents, technical documentation, financial reports, internal knowledge bases. Last month I was evaluating a RAG pipeline for a fintech company. Their retrieval metrics were excellent. Precision above 90%. They were proud of those numbers and they should have been. Then I ran a set of queries that involved policy documents updated in the past year, the kind of questions a compliance officer would ask on a Tuesday morning, and the system confidently cited the superseded policy on four out of ten queries. Same pipeline, same embeddings, same vector store. The only difference was whether the query touched documents that had been updated. That is the moment the team stopped talking about retrieval and started talking about what happens after retrieval.

I'm going to walk you through the three failure patterns that show up everywhere and then lay out a three-layer evaluation architecture for catching them. The failure patterns are structural. They appear regardless of the embedding model, regardless of the vector database, regardless of the LLM doing the synthesis. These are not configuration issues you can tune away.

**Failure mode one: temporal collision.** The system retrieves chunks from documents written at different points in time and treats them as simultaneously true. Your 2024 pricing policy says enterprise contracts start at $50,000 annually. Your 2025 pricing policy says $75,000. Both are in the vector database. Both are semantically similar to the query "what is our enterprise pricing?" The model retrieves both, and instead of identifying the conflict and surfacing the most current answer, it either picks one without telling you which, averages them into something neither document says, or confidently states the outdated figure because it appeared in a longer, more detailed document that the model weighted more heavily.

This is not a retrieval problem. Both documents were correctly retrieved. It is an assembly problem. The model has no reliable mechanism for temporal reasoning across chunks that lack explicit date metadata in the text itself.

Think about what a good research librarian does when you ask a question and she finds two sources that contradict each other. She does not blend them. She tells you: "The 2024 edition says X. The 2025 edition says Y. Which timeframe are you asking about?" The model skips that step entirely. It merges the sources and hands you a confident answer that neither source supports.

What does good look like for temporal collision? A system that detects date-bearing chunks in the retrieved set and either surfaces the most recent by default with a note that older versions exist, or asks the user to specify a timeframe. What does bad look like? What most teams have today. The model picks a source based on embedding similarity or chunk length, the user has no idea which version they got, and the answer might be eighteen months out of date.

**Failure mode two: scope bleed.** The system retrieves chunks that are individually correct but apply to different contexts, and the model merges them. Your engineering documentation says the API rate limit is 1,000 requests per minute. That is true for the public API. Your internal documentation says there is no rate limit. That is true for the internal service mesh. A developer asks "what is the API rate limit?" and gets back an answer that combines both contexts into something like "the rate limit is 1,000 requests per minute, though this can be bypassed for internal services." That sounds helpful. It is also a security-relevant disclosure that should never have been assembled from those two sources together in that way.

This is the equivalent of a pharmacist reading two prescription labels, one for you and one for the patient before you, and giving you a combined dosage instruction. Both labels are correct. Combining them is dangerous. And the pharmacist would never do that because pharmacists are trained to verify scope, which patient this applies to, before acting on any piece of information. Models doing RAG synthesis have no equivalent of that verification step.

Again, retrieval worked. Both chunks were relevant to the query. The failure is in assembly. The model cannot reliably distinguish scope boundaries across retrieved chunks.

**Failure mode three: confidence inheritance.** The model retrieves a mix of authoritative and speculative content and presents the synthesis with the confidence level of the most authoritative source. Your approved product roadmap says feature X ships in Q3. A Slack thread from an engineer says "we might also ship feature Y if we have bandwidth." The RAG system retrieves both and responds: "Features X and Y are planned for Q3." The speculative content inherited the confidence of the authoritative content through the act of assembly.

Yoshua Bengio's group at Mila published research in 2024 showing that language models systematically fail to propagate uncertainty through multi-step reasoning. When one premise is uncertain, the conclusion should inherit that uncertainty. Instead, models tend to converge on confident outputs regardless of input uncertainty. That finding was about reasoning chains, but the mechanism is identical in RAG assembly. Uncertain inputs produce confident outputs because the model has no architecture for tracking provenance and confidence separately.

This one is particularly hard to catch because the answer is not wrong in the way that triggers traditional evals. It is directionally plausible. It contains real information. It just presents speculation as commitment, and that distinction matters enormously when the person reading the answer is a customer, an executive, or an auditor.

And here's the thing. This is not just an AI problem. It is exactly the failure mode that gets journalists fired. A reporter who takes an on-the-record statement from a CEO and a rumour from an anonymous source and presents both with equal confidence in the same paragraph has committed a basic journalistic error. Newsrooms have editorial standards specifically to prevent this. Your RAG pipeline has no equivalent editorial layer. It assembles sources with mixed authority into a single confident voice, every single time.

## The RAG Fidelity Stack

Before you jump to the conclusion that I am telling you to abandon RAG, I am not. RAG is the right architecture for grounding language models in your data. The issue is not the pattern. It is the gap between how teams build RAG systems and how they evaluate them.

I call this the RAG Fidelity Stack. It has three layers, and most teams only have the first one.

**Layer one: retrieval quality.** Are the right chunks being retrieved? This is what most teams measure. Precision, recall, MRR, NDCG. Pinecone published benchmarks last year showing that hybrid search with reranking can push retrieval precision above 90% on well-structured corpora. These metrics are well understood, well tooled, and necessary. They are also insufficient on their own.

**Layer two: assembly fidelity.** Given correctly retrieved chunks, does the model's synthesised answer faithfully represent what those chunks actually say? This requires comparing the final answer against the source chunks and checking for temporal collisions, scope bleeds, and confidence inheritance. You can build this with an LLM-as-judge pattern, but the judge needs specific rubrics for each failure mode, not a generic "is this answer correct?" prompt. Ragas, the open source RAG evaluation framework, provides faithfulness and answer relevancy metrics that get at this layer, and teams using it report catching assembly errors that their retrieval metrics completely missed.

**Layer three: boundary honesty.** When the retrieved chunks do not contain enough information to fully answer the question, does the system say so? Or does it fill the gap with plausible-sounding extrapolation and present it as grounded? This is the hardest layer to test and the one with the highest cost when it fails, because the whole point of RAG is to ground the model in your data. If the system silently switches from grounded to ungrounded mid-answer, the user has no way to tell where the boundary is.

What does bad look like? Testing only layer one and celebrating 90% retrieval precision while your assembly layer introduces errors on 20% of multi-source queries. Or worse, testing all three layers once during development and never again, while your document corpus grows and shifts underneath the frozen eval set. That is not evaluation. That is a snapshot.

## Same Pipeline, Different Evaluation, Different Outcome

I want to make this concrete. I have seen two teams with nearly identical RAG architectures. Same embedding model, same vector database, same LLM for synthesis. Team A tested retrieval quality obsessively. They built dashboards. They tracked precision and recall weekly. Their retrieval metrics were best in class. But they never tested what the model did with the retrieved chunks. Team B had decent retrieval, nothing special, but they built assembly-level evals. They tested for temporal conflicts, scope boundaries, and confidence mixing using their own documents. Six months in, Team A's system had silently drifted. Updated documents were creating temporal collisions that nobody caught because the retrieval metrics still looked great. Team B caught the same class of errors within days because their evals were designed to surface them.

Same architecture. Same tools. Different evaluation discipline. Dramatically different trust outcomes. The difference was not technology. It was whether the humans building the system understood that retrieval quality and answer quality are not the same measurement.

## This Pattern Is Not New

Let's be honest. The assembly problem in RAG is not actually a novel failure mode. It is the same problem that has shown up in every domain where humans or machines have to synthesise information from multiple sources under time pressure.

Intelligence analysis has dealt with this for decades. The 9/11 Commission Report documented how individual intelligence agencies each had correct fragments of information, but the assembly of those fragments into a coherent threat assessment failed catastrophically. The data was retrieved. The synthesis was wrong. The commission's core recommendation was not better collection. It was better integration, a structural fix to the assembly layer.

Medical diagnosis follows the same pattern. A 2023 study in BMJ Quality and Safety found that diagnostic errors in hospitals are most commonly caused not by missing information but by the incorrect integration of available information. The right test results were in the chart. The synthesis into a diagnosis went wrong. Same retrieval, broken assembly.

And it is the same pattern in academic peer review. Reviewers who read five papers on a topic and write a literature review must decide which findings to weight, which contradict, which apply in which context. The quality of the review is not determined by whether they found the papers. It is determined by whether they assembled the findings faithfully. Three independent disciplines. Same conclusion. The hard part is never the retrieval. It is the assembly.

## What This Means for Your Team

If you are an engineer building a RAG pipeline, start logging the retrieved chunks alongside every answer, not just the final output. You cannot debug assembly failures without seeing what the model was working with. Build at least five eval cases for each of the three assembly failure modes using your actual documents. Temporal conflicts are the easiest to construct and the most immediately revealing. If you have documents that were updated in the past year, you already have the test data. Use it.

If you manage a team shipping RAG to users, ask your engineers a simple question: what happens when the system retrieves contradictory information? If the answer is "we haven't tested that," you have a gap that matters more than your next feature. Every document update, every policy change, every new data source creates potential temporal collisions in your pipeline, and the failure rate compounds over time as your corpus grows. The system that worked at 500 documents may fail at 5,000. Not because retrieval degraded, but because the assembly problem gets harder as the source material gets more internally contradictory.

If you run an organisation that is investing in RAG as a knowledge management strategy, understand that retrieval is table stakes and assembly quality is the differentiator. The vendors who can show you assembly-level evals, not just retrieval metrics, are the ones building systems that will hold up when the stakes are real. Ask them: "How do you handle temporal conflicts in the retrieved context?" If they talk about embeddings, they have not solved the problem.

## The Bigger Picture

RAG is following the same maturity curve as every other AI production pattern. The first generation of adopters built it, shipped it, and measured what was easy to measure. Retrieval metrics are easy. Assembly fidelity is hard. And so the industry optimised for retrieval while the real failure mode sat in the synthesis layer, quietly generating answers that were wrong in ways that standard evals could not catch.

This is not unique to RAG. It is the same pattern in agent evaluation, where the Mount Sinai health study found that ChatGPT Health could correctly identify respiratory failure in its reasoning trace and then recommend waiting 48 hours in its output. It is the same pattern in coding assistants, where the generated code handles the happy path and breaks on edge cases that the model never flagged. Everywhere you look, the gap between "looks right" and "is right" is the gap that determines whether the system creates value or liability. And everywhere you look, that gap lives in the assembly layer, not the retrieval layer.

The teams that figure out how to test for assembly fidelity are the ones whose systems will actually be trusted by the humans who depend on them. And trust, once lost to a confident wrong answer delivered from your own documents, is very expensive to rebuild.

So look at your RAG pipeline. Look at whether you are testing retrieval or testing the whole system. Build the assembly evals. I know they are not glamorous work. But they are the difference between a system that sounds right and a system that is right. And in a world where AI made volume free, correctness is the only thing that matters.

Cheers.
