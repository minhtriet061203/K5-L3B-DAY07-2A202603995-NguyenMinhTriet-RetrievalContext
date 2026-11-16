| id | gold | bm25_k3_b4000 | bm25_rerank_k3_b4000 |
|---|---|---|---|
| q01 | p14 | answer s1 ctx:Y p[14,18,22] | answer s1 ctx:Y p[14,22,73] |
| q02 | p19 | answer s1 ctx:N p[17,14,16] | answer s1 ctx:Y p[17,16,19] |
| q03 | p20 | answer s1 ctx:Y p[15,17,20] | answer s1 ctx:Y p[20,21,21] |
| q04 | p22 | answer s1 ctx:Y p[22,54,28] | answer s1 ctx:Y p[22,21,28] |
| q05 | p25 | answer s1 ctx:Y p[25,26,28] | answer s1 ctx:Y p[25,26,28] |
| q06 | p26 | answer s1 ctx:Y p[26,29,36] | answer s1 ctx:Y p[26,29,23] |
| q07 | p28 | answer s1 ctx:N p[28,28,33] | answer s1 ctx:Y p[28,28,28] |
| q08 | p34 | answer s1 ctx:Y p[34,44,43] | answer s1 ctx:Y p[34,42,43] |
| q09 | p35 | answer s1 ctx:Y p[35,48,38] | answer s1 ctx:Y p[35,38,38] |
| q10 | p40 | answer s1 ctx:Y p[40,33,40] | answer s2 ctx:Y p[40,59,20,40,40] |
| q11 | p43 | answer s1 ctx:Y p[43,44,43] | answer s1 ctx:Y p[43,42,43] |
| q12 | p45 | answer s1 ctx:Y p[46,45,35] | answer s1 ctx:Y p[45,41,20] |
| q13 | p55 | answer s1 ctx:Y p[47,55,50] | answer s1 ctx:Y p[55,50,47] |
| q14 | p44 | answer s1 ctx:Y p[44,41,44] | answer s1 ctx:Y p[44,17,41] |
| q15 | p56 | answer s1 ctx:Y p[56,47,50] | answer s3 ctx:Y p[47,59,50,56,61] |
| u01 | none | abstai s3 ctx:- p[55,21,29,21,24] | abstai s3 ctx:- p[24,29,18,21,30] |
| u02 | none | abstai s1 ctx:- p[40,40,43] | abstai s1 ctx:- p[40,40,40] |

Abstain / error reasons:
- u01 / bm25_k3_b4000: abstain - The report does not specify the learning rate or number of training epochs for adversarial training against evasion attacks.
- u01 / bm25_rerank_k3_b4000: abstain - The passages do not contain specific recommendations for learning rate or number of training epochs for adversarial training against evasion
- u02 / bm25_k3_b4000: abstain - The passages do not provide specific information about the monetary loss incurred by Microsoft due to the Tay.AI incident.
- u02 / bm25_rerank_k3_b4000: abstain - The passages do not contain information regarding the financial loss incurred by Microsoft due to the Tay.AI incident.
