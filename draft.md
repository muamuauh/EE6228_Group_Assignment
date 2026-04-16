# Mathematical Modeling and Optimization of Meal Preparation Scheduling in a Small Restaurant Kitchen

**Course:** Process Modeling and Scheduling  
**Group members:** [Name 1], [Name 2], [Name 3], [Name 4], [Name 5]  
**Submission format:** DOC or PDF

## 1. Introduction and Problem Description

### 1.1 Background and Project Objective

Scheduling problems are common in systems where multiple tasks must share limited resources [1], [2]. Besides manufacturing and logistics, similar problems also appear in restaurant kitchens, where different dishes compete for preparation and cooking resources. In this project, we model a small restaurant kitchen as a scheduling system and study how to arrange dish-preparation operations efficiently.

The objective of this project is to formulate the meal preparation process as an optimization problem and determine a schedule that minimizes the overall completion time, also called the makespan [1]. Through this use case, we show how a practical kitchen workflow can be transformed into a standard scheduling problem and solved using mathematical optimization methods.

### 1.2 Use Case and Assumptions

The use case considered in this project is a small restaurant kitchen preparing five dishes during the same service period: fried rice, grilled chicken, baked pasta, vegetable salad, and omelette. The kitchen contains limited shared resources, including one preparation station, two stove positions, one oven, and one plating station.

To keep the problem manageable, the following assumptions are made:

1. All dishes are available at time zero.
2. Each operation is non-preemptive once started.
3. Processing times are known and fixed in advance.
4. Setup time, cleaning time, and transportation delay between stations are ignored.
5. Each resource can process at most one operation at a time.
6. The resource assigned to each operation is fixed in the input data.

Under these assumptions, the kitchen scheduling problem can be modeled as a small job-shop scheduling problem with precedence constraints and resource capacity constraints [3], [4].

## 2. Input Data

### 2.1 Dishes and Operations

The following table defines the dish operations, required resources, and processing times.

| Dish | Operation | Resource | Processing time |
|---|---|---|---:|
| Fried rice | FR-1: ingredient preparation | Prep | 4 min |
| Fried rice | FR-2: wok cooking | Stove 1 | 8 min |
| Fried rice | FR-3: plating | Plate | 2 min |
| Grilled chicken | GC-1: marinating and preparation | Prep | 5 min |
| Grilled chicken | GC-2: grilling | Stove 2 | 12 min |
| Grilled chicken | GC-3: plating | Plate | 3 min |
| Baked pasta | BP-1: ingredient preparation | Prep | 6 min |
| Baked pasta | BP-2: baking | Oven | 15 min |
| Baked pasta | BP-3: plating | Plate | 3 min |
| Vegetable salad | VS-1: washing and cutting | Prep | 4 min |
| Vegetable salad | VS-2: plating | Plate | 2 min |
| Omelette | OM-1: ingredient preparation | Prep | 3 min |
| Omelette | OM-2: pan cooking | Stove 1 | 5 min |
| Omelette | OM-3: plating | Plate | 2 min |

### 2.2 Resource Configuration

The kitchen resources are:

| Resource | Capacity | Description |
|---|---:|---|
| Prep | 1 | Shared preparation station |
| Stove 1 | 1 | Cooking resource for fried rice and omelette |
| Stove 2 | 1 | Cooking resource for grilled chicken |
| Oven | 1 | Baking resource for baked pasta |
| Plate | 1 | Shared plating station |

## 3. Mathematical Formulation

### 3.1 Sets and Parameters

Let the set of dishes be:

$$
J = \{FR, GC, BP, VS, OM\}
$$

where FR, GC, BP, VS, and OM represent fried rice, grilled chicken, baked pasta, vegetable salad, and omelette.

Let the set of kitchen resources be:

$$
R = \{Prep, Stove1, Stove2, Oven, Plate\}
$$

Each dish j contains a sequence of operations:

$$
O_j = \{1,2,\ldots,n_j\}
$$

For each operation, the following parameters are defined:

$$
p_{jk} = \text{processing time of operation } k \text{ of dish } j
$$

$$
r_{jk} = \text{resource required by operation } k \text{ of dish } j
$$

### 3.2 Decision Variables

The main continuous decision variable is the starting time:

$$
s_{jk} = \text{starting time of operation } k \text{ of dish } j
$$

The makespan is:

$$
C_{\max} = \text{completion time of the last finished dish}
$$

For any two operations a and b that require the same exclusive resource, a binary sequencing variable is introduced:

$$
x_{ab} =
\begin{cases}
1, & \text{if operation } a \text{ is scheduled before operation } b \\
0, & \text{otherwise}
\end{cases}
$$

### 3.3 Objective Function

The objective is to minimize the makespan:

$$
\min C_{\max}
$$

This means that the kitchen aims to complete all five dishes as early as possible.

### 3.4 Constraints

First, each dish must follow its required operation order. The next operation cannot start before the previous operation is completed:

$$
s_{j,k+1} \geq s_{jk} + p_{jk}, \quad \forall j \in J,\; k=1,\ldots,n_j-1
$$

Second, if two operations require the same exclusive resource, they cannot overlap. For any two such operations a and b:

$$
s_a + p_a \leq s_b + M(1-x_{ab})
$$

$$
s_b + p_b \leq s_a + Mx_{ab}
$$

where M is a sufficiently large positive constant.

Third, the completion time of the last operation of each dish must not exceed the makespan:

$$
s_{j,n_j} + p_{j,n_j} \leq C_{\max}, \quad \forall j \in J
$$

Fourth, the starting times and makespan must be non-negative:

$$
s_{jk} \geq 0, \quad C_{\max} \geq 0
$$

Finally, the sequencing variable is binary:

$$
x_{ab} \in \{0,1\}
$$

Under these constraints, the kitchen scheduling problem is formulated as a mixed-integer optimization problem following standard scheduling-modeling ideas [1], [2].

## 4. Solution Strategy and Tool Description

### 4.1 CP-SAT Optimization Approach

The kitchen scheduling problem includes both time decisions and sequencing decisions. Therefore, it cannot be solved by a simple analytical formula. In this project, the model is solved using Python and Google OR-Tools CP-SAT [5], [6].

CP-SAT is suitable for this problem because it can directly model discrete scheduling decisions, precedence constraints, and non-overlap constraints on shared resources [5], [6]. Each kitchen operation is represented as an interval variable with a start time, a fixed processing duration, and an end time. For example, the preparation operation of fried rice is modeled as one interval assigned to the Prep resource.

For each dish, precedence constraints are added to ensure that its operations follow the correct process order. For each resource, a NoOverlap constraint is added to prevent two operations from being processed at the same time, which is consistent with the job-shop scheduling example in OR-Tools [4]. The makespan variable C<sub>max</sub> is linked to the end time of the last operation of every dish, and the solver minimizes C<sub>max</sub>.

### 4.2 Tool Description

The implementation tool is Google OR-Tools CP-SAT, called from Python. The main modeling components are:

| Component | Role in this project |
|---|---|
| `NewIntVar` | Creates integer start-time, end-time, and makespan variables. |
| `NewIntervalVar` | Creates an operation interval with start time, duration, and end time. |
| `Add` | Adds precedence constraints and makespan constraints. |
| `AddNoOverlap` | Ensures that operations using the same resource do not overlap. |
| `Minimize` | Sets the objective to minimize C<sub>max</sub>. |
| `CpSolver` | Solves the CP-SAT model and returns operation start and finish times. |

This tool is appropriate for the small restaurant kitchen case and can also be extended to larger cases with more dishes, due dates, alternative resources, setup times, and priority rules [3], [4].

### 4.3 Implementation Procedure

The implementation procedure is:

1. Define dishes, operations, processing times, and required resources.
2. Create start-time, end-time, and interval variables for each operation.
3. Add precedence constraints for each dish.
4. Add NoOverlap constraints for Prep, Stove 1, Stove 2, Oven, and Plate.
5. Define C<sub>max</sub> as the maximum completion time of all dishes.
6. Minimize C<sub>max</sub> using the CP-SAT solver.
7. Extract the optimal start and finish times from the solver output.
8. Visualize the final schedule using a Gantt chart.

## 5. Results and Discussion

### 5.1 Optimal Scheduling Result

The optimal schedule found by the Python + Google OR-Tools CP-SAT model has:

$$
C_{\max} = 31 \text{ minutes}
$$

The detailed operation schedule is:

| Dish | Operation | Resource | Start | Finish |
|---|---|---|---:|---:|
| Baked pasta | BP-1: ingredient preparation | Prep | 0 | 6 |
| Baked pasta | BP-2: baking | Oven | 6 | 21 |
| Omelette | OM-1: ingredient preparation | Prep | 6 | 9 |
| Grilled chicken | GC-1: marinating and preparation | Prep | 9 | 14 |
| Omelette | OM-2: pan cooking | Stove 1 | 9 | 14 |
| Omelette | OM-3: plating | Plate | 14 | 16 |
| Fried rice | FR-1: ingredient preparation | Prep | 14 | 18 |
| Grilled chicken | GC-2: grilling | Stove 2 | 14 | 26 |
| Vegetable salad | VS-1: washing and cutting | Prep | 18 | 22 |
| Fried rice | FR-2: wok cooking | Stove 1 | 18 | 26 |
| Baked pasta | BP-3: plating | Plate | 21 | 24 |
| Vegetable salad | VS-2: plating | Plate | 24 | 26 |
| Fried rice | FR-3: plating | Plate | 26 | 28 |
| Grilled chicken | GC-3: plating | Plate | 28 | 31 |

The Gantt chart below visualizes the schedule.

![Gantt chart of the optimal kitchen schedule](gantt_chart.svg)

### 5.2 Resource Utilization

Resource utilization is calculated as:

$$
U_r = \frac{\sum p_{jk} \text{ for operations assigned to resource } r}{C_{\max}} \times 100\%
$$

The utilization values are:

| Resource | Workload | Makespan | Utilization |
|---|---:|---:|---:|
| Prep | 22 min | 31 min | 70.97% |
| Stove 1 | 13 min | 31 min | 41.94% |
| Stove 2 | 12 min | 31 min | 38.71% |
| Oven | 15 min | 31 min | 48.39% |
| Plate | 12 min | 31 min | 38.71% |

![Resource utilization chart](machine_utilization.svg)

The preparation station has the highest utilization at 70.97%, so it is the main bottleneck in this schedule. This result is reasonable because all five dishes require preparation before cooking or plating. The oven is also relatively important because baked pasta requires a long 15-minute baking operation, but it does not become the main bottleneck because only one dish uses the oven.

The plating station is used intermittently in the second half of the schedule. Its workload is only 12 minutes, but poor ordering on the plating station can still delay final dish completion. In the optimal schedule, plating is arranged in the order omelette, baked pasta, vegetable salad, fried rice, and grilled chicken, so the final dish is completed at minute 31 without unnecessary resource conflicts.

## 6. Simulation Demo

A simple simulation demo can be implemented using the optimal operation table. At each minute, the system checks which operation is active on each resource and updates the kitchen status.

The simulation logic is:

1. Initialize current time t = 0.
2. For each resource, check whether an operation interval satisfies start &le; t < finish.
3. Display the active operation on Prep, Stove 1, Stove 2, Oven, and Plate.
4. Increase t until t = C<sub>max</sub>.

The static Gantt chart in this report can be treated as a visual summary of the simulation. A dynamic version could highlight the active operations from minute 0 to minute 31.

## 7. Conclusion

This project modeled a small restaurant kitchen as a job-shop scheduling problem. Five dishes were divided into ordered operations, and each operation was assigned to a limited kitchen resource. A mathematical optimization model was constructed with precedence constraints, resource-capacity constraints, and a makespan-minimization objective [1], [4].

Using the Python + Google OR-Tools CP-SAT model, the optimal makespan was found to be 31 minutes. The result shows that the preparation station is the main bottleneck, while the oven and stove resources are less heavily utilized. The model is simple enough for a course project, but it can be extended to include alternative resources, due dates, setup times, cleaning times, or priority orders [3], [5].

## 8. References

[1] Pinedo, M. L. (2016). *Scheduling: Theory, Algorithms, and Systems*. Springer.

[2] Brucker, P. (2007). *Scheduling Algorithms*. Springer.

[3] Google OR-Tools. *Scheduling Overview*. https://developers.google.com/optimization/scheduling

[4] Google OR-Tools. *The Job Shop Problem*. https://developers.google.com/optimization/scheduling/job_shop

[5] Google OR-Tools. *CP-SAT Solver*. https://developers.google.com/optimization/cp/cp_solver

[6] Google OR-Tools. *How to Cite OR-Tools and Its Solvers*. https://developers.google.com/optimization/support/cite
