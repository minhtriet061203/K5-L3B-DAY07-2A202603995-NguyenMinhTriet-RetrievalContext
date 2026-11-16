| id | gold | dense_k3_b800 | bm25_k3_b800 | hybrid_k3_b800 |
|---|---|---|---|---|
| q01 | p14 | abstai s3 ctx:N p[28] | answer s1 ctx:Y p[14] | answer s1 ctx:Y p[14] |
| q02 | p19 | abstai s3 ctx:N p[15] | abstai s3 ctx:N p[-] | abstai s3 ctx:N p[47] |
| q03 | p20 | answer s1 ctx:Y p[20] | abstai s3 ctx:N p[15] | answer s1 ctx:Y p[20] |
| q04 | p22 | answer s1 ctx:N p[28] | abstai s3 ctx:N p[21] | answer s1 ctx:N p[28] |
| q05 | p25 | answer s1 ctx:Y p[25] | abstai s2 ctx:Y p[25] | abstai s1 ctx:Y p[25] |
| q06 | p26 | abstai s3 ctx:N p[29] | abstai s3 ctx:N p[29] | abstai s3 ctx:N p[29] |
| q07 | p28 | answer s1 ctx:Y p[28] | answer s1 ctx:Y p[28] | abstai s3 ctx:N p[28] |
| q08 | p34 | abstai s3 ctx:N p[53] | abstai s3 ctx:N p[44] | abstai s3 ctx:N p[44] |
| q09 | p35 | answer s1 ctx:Y p[35] | answer s1 ctx:Y p[35] | answer s1 ctx:Y p[35] |
| q10 | p40 | abstai s1 ctx:N p[40] | abstai s3 ctx:N p[33,40] | answer s1 ctx:N p[40] |
| q11 | p43 | abstai s3 ctx:N p[42] | abstai s3 ctx:N p[44] | abstai s3 ctx:N p[44] |
| q12 | p45 | abstai s3 ctx:N p[46] | abstai s3 ctx:N p[46,41] | abstai s3 ctx:N p[46] |
| q13 | p55 | abstai s3 ctx:N p[55] | abstai s3 ctx:N p[47] | abstai s3 ctx:N p[59] |
| q14 | p44 | abstai s3 ctx:N p[45] | abstai s3 ctx:N p[45] | abstai s3 ctx:N p[28] |
| q15 | p56 | abstai s3 ctx:N p[47] | abstai s3 ctx:N p[47] | answer s1 ctx:Y p[56] |
| u01 | none | abstai s3 ctx:- p[28] | abstai s3 ctx:- p[55] | abstai s2 ctx:- p[24,28] |
| u02 | none | abstai s1 ctx:- p[40] | abstai s3 ctx:- p[40] | abstai s3 ctx:- p[40] |

Abstain / error reasons:
- q01 / dense_k3_b800: abstain - There are no passages that explicitly define or describe what the field of adversarial machine learning studies.
- q02 / dense_k3_b800: abstain - The passages did not contain specific information about the three attacker objectives used to classify attacks on predictive AI systems.
- q02 / bm25_k3_b800: abstain - The passages do not contain information about the three attacker objectives used to classify attacks on predictive AI systems.
- q02 / hybrid_k3_b800: abstain - The passages do not specify the three attacker objectives used to classify attacks on predictive AI systems.
- q03 / bm25_k3_b800: abstain - The passages do not explicitly mention a specific attack that requires the attacker to control both training and test data.
- q04 / bm25_k3_b800: abstain - The searched passages do not contain specific information about the assumptions related to the attacker's knowledge in black-box attacks.
- q05 / bm25_k3_b800: abstain - The passages do not provide specific information about the number of iterations performed by the iterative FGSM method.
- q05 / hybrid_k3_b800: abstain - The passages indicate that FGSM performs a single iteration of gradient descent, but do not specify the number of iterations for the iterati
- q06 / dense_k3_b800: abstain - No specific details about how researchers fooled a traffic sign recognition model in the physical world were found.
- q06 / bm25_k3_b800: abstain - The passages do not provide specific information on how researchers fooled a traffic sign recognition model in the physical world.
- q06 / hybrid_k3_b800: abstain - The searched passages did not provide specific details on how researchers fooled a traffic sign recognition model in the physical world.
- q07 / hybrid_k3_b800: abstain - The passages do not contain specific information about popular methods for estimating model gradients in score-based black-box evasion attac
- q08 / dense_k3_b800: abstain - The searched passages do not contain information specifically about the conditions under which the RONI method excludes a sample from traini
- q08 / bm25_k3_b800: abstain - The report does not provide specific conditions under which the RONI method excludes a sample from training.
- q08 / hybrid_k3_b800: abstain - The passages retrieved do not provide specific information regarding the conditions under which the RONI method excludes a sample from train
- q10 / dense_k3_b800: abstain - The passage only mentions the Tay.AI chatbot without providing specific details or context about being the earliest documented case.
- q10 / bm25_k3_b800: abstain - The passages do not specify which Microsoft chatbot was the earliest documented case of an attack.
- q11 / dense_k3_b800: abstain - The passages do not provide specific criteria or conditions under which a target sample is judged to be part of the training set in the cont
- q11 / bm25_k3_b800: abstain - The passages do not contain information specifically about when a target sample is judged to be part of the training set in a loss-based mem
- q11 / hybrid_k3_b800: abstain - The passages do not contain specific information about when a target sample is judged to be part of the training set in the context of loss-
- q12 / dense_k3_b800: abstain - The passages do not specifically address whether differential privacy protects against model extraction attacks.
- q12 / bm25_k3_b800: abstain - The passages do not explicitly state whether differential privacy protects against model extraction attacks.
- q12 / hybrid_k3_b800: abstain - The passages do not specifically address whether differential privacy protects against model extraction attacks.
- q13 / dense_k3_b800: abstain - The passages do not specifically describe how an attacker can poison a training dataset published as a list of URLs.
- q13 / bm25_k3_b800: abstain - The passages do not provide information on how an attacker can poison a training dataset published as a list of URLs in generative AI system
- q13 / hybrid_k3_b800: abstain - The passages do not contain specific information on how an attacker can poison a training dataset published as a list of URLs.
- q14 / dense_k3_b800: abstain - The passages do not explicitly define the goal of a model extraction attack in the context of MLaaS.
- q14 / bm25_k3_b800: abstain - The passages do not explicitly state the specific goal of model extraction attacks in the context of MLaaS.
- q14 / hybrid_k3_b800: abstain - The passages do not contain specific information about the goal of model extraction attacks for predictive AI models offered through MLaaS.
- q15 / dense_k3_b800: abstain - The passages do not contain information on checking for integrity of downloaded training data for generative AI models.
- q15 / bm25_k3_b800: abstain - The passages do not provide information on how to check the integrity of training data for generative AI models.
- u01 / dense_k3_b800: abstain - The report does not provide specific information on the recommended learning rate or number of training epochs for adversarial training agai
- u01 / bm25_k3_b800: abstain - The passages do not contain specific information about the recommended learning rate and number of training epochs for adversarial training 
- u01 / hybrid_k3_b800: abstain - The passages do not contain specific recommendations for the learning rate and number of training epochs for adversarial training against ev
- u02 / dense_k3_b800: abstain - The passages do not provide specific information about the financial loss Microsoft incurred from the Tay.AI incident.
- u02 / bm25_k3_b800: abstain - The passages do not contain any information regarding the monetary loss Microsoft incurred due to the Tay.AI chatbot incident.
- u02 / hybrid_k3_b800: abstain - The report does not provide any information regarding the financial loss Microsoft incurred due to the Tay.AI chatbot incident.
