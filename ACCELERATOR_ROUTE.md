# Accelerator route: from public evidence to serious compute

The sequence matters: publish the instrument, show the reference result, then
submit the same bounded experiment through several legitimate doors.

## 1. NVIDIA Inception + Innovation Lab

**Best direct GPU route.** Join NVIDIA Inception, publish the repository and
product profile, then apply separately to the Innovation Lab. The lab describes
a 60-day accelerator with GPU instances for selected Inception members.

Use `applications/NVIDIA_INNOVATION_LAB.md` as the form-answer source. Ask for
four H100-class GPUs but state that the experiment scales down cleanly.

- Inception: https://www.nvidia.com/en-us/startups/
- Innovation Lab: https://www.nvidia.com/en-us/data-center/innovation-lab/

## 2. Google TPU Research Cloud

**Best open-research route.** Submit the public benchmark as a research proposal
and commit to releasing code, results, failures, and a report. TPU Research
Cloud states that it provides researchers free access to a cluster of more than
1,000 Cloud TPUs.

Use `applications/GOOGLE_TPU_RESEARCH_CLOUD.md`; the first awarded milestone is
a deterministic JAX port with parity tests against this Python reference.

- Program: https://sites.research.google/trc/

## 3. Immediate startup credits

Use these for the website, registry, small sweeps, and evidence needed for the
larger applications—not as a substitute for a research plan.

- Google for Startups offers a $2,000 path for early, unfunded startups and a
  larger AI tier for eligible funded companies:
  https://cloud.google.com/startup
- AWS Activate Founders describes $1,000 in credits for eligible self-funded
  startups; the Portfolio route requires an Activate Provider:
  https://aws.amazon.com/aws-startups/credits
- Microsoft for Startups documents initial credit tiers after identity and
  business verification, with additional milestones tied to verified Azure
  usage:
  https://learn.microsoft.com/en-us/startups/microsoft-for-startups/getting-started-mfs

## Submission packet

Send the same five items everywhere:

1. public repository URL;
2. the `results/reference.json` output and reproduction command;
3. one-page application draft matched to the program;
4. eight-week experiment plan with measurable deliverables;
5. a direct statement of what would falsify the hypothesis.

## Honest one-line pitch

> We built a reproducible instrument for measuring whether relational meaning
> survives representation changes; accelerator access lets us test it across
> millions of multimodal states and publish the failures as rigorously as the
> successes.

## What not to lead with

Do not lead with consciousness, perpetual energy, legal invulnerability, or
global reform. Those claims are not measured by TPSI-1. Lead with the runnable
experiment, the controls, and the public result.
