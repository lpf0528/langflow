
# 1、知识库检索节点


## 1、模型
```python
embedding_model = get_model_instance_by_model_workspace_id(model_id, workspace_id)
```
## 2、向量化问题
```python
embedding_value = embedding_model.embed_query(question)
```

## 3、获取向量存储
```python
vector = VectorStore.get_embedding_vector()
```

## 4、查询Embedding数据表
参数说明：
1024: 问题的向量维度长度(len(embedding_value))
[0.04184545, 0.003414726, -0.010979685]：问题的向量表示（json.dumps(query_embedding)）
UUID('019bbc03-61b0-7e60-a710-f7b0e8f19fca')：知识库ID（knowledge_id）
0.6：相似度阈值（threshold）
3：引用分段TOP（top_number）

```sql
SELECT
paragraph_id,
comprehensive_score,
comprehensive_score AS similarity
FROM
  (
    SELECT DISTINCT ON
      ("paragraph_id") (1 - distance),* ,
      (1 - distance) AS comprehensive_score
    FROM
      (
        SELECT
          *,
          (embedding.embedding :: vector (1024) <=>  '[0.04184545, 0.003414726, -0.010979685]') AS distance
        FROM
          embedding
        WHERE
          ("embedding"."is_active" AND "embedding"."knowledge_id" IN (UUID('019bbc03-61b0-7e60-a710-f7b0e8f19fca'), UUID('019bbb82-77d6-7e93-ba5f-0594ba8f4f11')))
        ORDER BY
          distance
      ) TEMP
    ORDER BY
      paragraph_id,
      distance
  ) DISTINCT_TEMP
WHERE
  comprehensive_score > 0.6
ORDER BY
  comprehensive_score DESC
  LIMIT 3
```

## 5、将查询结果转换为引用分段放在提示词中