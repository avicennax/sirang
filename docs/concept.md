# SKEET - Simon's Komputational Expert Experiment Tracker

Assumptions:
- Experiment parameters are largely not hard coded.

Types of data to be stored:
- experiment meta-data: time, iterations, seeds etc.
- experiment data/outcomes: loss/perfomance, data statistics.
- experiment models: paths to model binary, parameters.

My use cases are storing model hyperparameters and/or seeds with corresponding performance.
as well as reloading hyperparameters/models data for continued training.

Design questions:
- When to store parameters?
- Call based store, i.e: decorators vs parameter dict based.


## Using MongoDB with decorators

Use MongoDB for storage with decorators to collect data.

### Ideas

- Basic approach would be one collection and each experiment is a single document. (1)

- A collection for each experiment, (e.g: documents could be based on seeded iterations) or a collection
with multiple document across multiple experiments along with collection where each document corresponds
to a single experiment, as described above.

ML/Neuro use case:
- Call some main script. (main)
- Load or generate data.
- Run n experiments m times perhaps with variation in m runs. (experiments)
