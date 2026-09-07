# After Confidence Improves, Fix Wrong Names

The user reports that champion-name results are better, but some champion names remain wrong.

The next step should not be an endless low-confidence loop. The user should move to targeted
wrong-name review:

1. Run the full combined hex pipeline.
2. Review final overlay images in `outputs/combined-hex-signals`.
3. Identify visible wrong champion names.
4. Save corrected champion crops into the true class folder, or `unknown` if the crop is bad.
5. Prioritize weak classes with low counts.
6. Retrain after enough useful corrected examples are added.

Important distinction: low-confidence review finds uncertain crops, while wrong-name review finds
model mistakes that remain after confidence improves.

The current weak classes include several Lux forms and other low-count classes. These should be
strengthened before expecting stable 75-class identity performance.
