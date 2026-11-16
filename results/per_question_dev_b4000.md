| id | gold | dense_k3_b4000 | bm25_k3_b4000 | hybrid_k3_b4000 |
|---|---|---|---|---|
| q01 | p14 | abstai s3 ctx:Y p[24,28,30,30,14] | answer s1 ctx:Y p[14,18,22] | answer s1 ctx:Y p[14,29,18] |
| q02 | p19 | answer s1 ctx:N p[17,16,57] | answer s1 ctx:N p[17,14,16] | answer s1 ctx:N p[17,18,16] |
| q03 | p20 | answer s1 ctx:Y p[21,20,17] | answer s1 ctx:Y p[15,17,20] | answer s1 ctx:N p[21,15,21] |
| q04 | p22 | answer s1 ctx:Y p[22,28,42] | answer s1 ctx:Y p[22,54,28] | answer s1 ctx:Y p[22,21,28] |
| q05 | p25 | answer s1 ctx:Y p[25,26,25] | answer s1 ctx:Y p[25,26,28] | answer s1 ctx:Y p[25,26,28] |
| q06 | p26 | answer s1 ctx:Y p[26,14,25] | answer s1 ctx:Y p[26,29,36] | answer s1 ctx:Y p[26,29,29] |
| q07 | p28 | answer s1 ctx:Y p[28,28,26] | answer s1 ctx:N p[28,28,33] | answer s1 ctx:Y p[28,28,33] |
| q08 | p34 | answer s1 ctx:Y p[34,59,37] | answer s1 ctx:Y p[34,44,43] | answer s1 ctx:Y p[34,59,44] |
| q09 | p35 | answer s1 ctx:Y p[35,38,19] | answer s1 ctx:Y p[35,48,38] | answer s1 ctx:Y p[35,38,55] |
| q10 | p40 | answer s1 ctx:Y p[40,40,18] | answer s1 ctx:Y p[40,33,40] | answer s1 ctx:Y p[40,27,40] |
| q11 | p43 | answer s1 ctx:Y p[43,42,43] | answer s1 ctx:Y p[43,44,43] | answer s1 ctx:Y p[43,43,44] |
| q12 | p45 | abstai s2 ctx:N p[20,41,46] | answer s1 ctx:Y p[46,45,35] | abstai s3 ctx:N p[46,20,35,41] |
| q13 | p55 | answer s1 ctx:Y p[55,50,48] | answer s1 ctx:Y p[47,55,50] | answer s1 ctx:Y p[55,50,59] |
| q14 | p44 | answer s1 ctx:Y p[44,41,20] | answer s1 ctx:Y p[44,41,44] | answer s1 ctx:Y p[44,41,45] |
| q15 | p56 | abstai s3 ctx:N p[50,47,59,49,49] | answer s1 ctx:Y p[56,47,50] | answer s1 ctx:Y p[56,59,55] |
| u01 | none | abstai s3 ctx:- p[30,24,28,30,24] | abstai s3 ctx:- p[55,21,29,21,24] | abstai s3 ctx:- p[24,28,30,24,29,25] |
| u02 | none | abstai s1 ctx:- p[40,40,40] | abstai s1 ctx:- p[40,40,43] | abstai s1 ctx:- p[40,40,40] |

Abstain / error reasons:
- q01 / dense_k3_b4000: abstain - The relevant passages do not provide a concise definition of adversarial machine learning; they discuss its study but lack a specific defini
- q12 / dense_k3_b4000: abstain - The passages do not specifically state whether differential privacy protects against model extraction attacks.
- q12 / hybrid_k3_b4000: abstain - The passages do not explicitly state whether differential privacy protects against model extraction attacks.
- q15 / dense_k3_b4000: abstain - The passages do not provide specific methods or techniques for checking the integrity of downloaded training data for generative AI models.
- u01 / dense_k3_b4000: abstain - The passages do not contain specific details about the recommended learning rate and number of training epochs for adversarial training agai
- u01 / bm25_k3_b4000: abstain - The report does not specify the learning rate or number of training epochs for adversarial training against evasion attacks.
- u01 / hybrid_k3_b4000: abstain - The passages do not specify the recommended learning rate and number of training epochs for adversarial training against evasion attacks.
- u02 / dense_k3_b4000: abstain - The passages do not provide specific information regarding the financial losses incurred by Microsoft due to the Tay.AI chatbot incident.
- u02 / bm25_k3_b4000: abstain - The passages do not provide specific information about the monetary loss incurred by Microsoft due to the Tay.AI incident.
- u02 / hybrid_k3_b4000: abstain - The passages do not provide information on the financial loss incurred by Microsoft due to the Tay.AI incident.
