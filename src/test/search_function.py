from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
import re
from sentence_transformers import SentenceTransformer

# Start your code here
# This is an outline, you can try any techniques you like.
# Please pay attention to the variable naming requirements below!

# Step 0: Load recipes
with open("data/recipes.json", encoding="utf-8") as f:
    recipe_data = json.load(f)

# Step 1: Create vector store
embedder = SentenceTransformer('all-MiniLM-L6-v2') # don't change the name of this variable! 
vector_store = list()                              # don't change the name of this variable! 

for recipe in recipe_data:
    # Append embeddings and recipe data to the vector_store list
    text = f"{recipe['title']}\n{recipe['instructions']}\n{recipe['ingredients']}"
    embedding = embedder.encode(text, convert_to_numpy=True)
    vector_store.append({
        "text": text,
        "embedding": embedding,
        "metadata": recipe
    })

# Step 2 - write search function
# don't rename this function! It's required for the testing code.
def search(embedder, vector_store, query, k, min_similarity):
    """
    根据查询中的属性返回相应的内容:
    - ingredients: 返回ingredients
    - instructions: 返回instructions
    - notes: 返回notes
    - serving size: 返回serving_size
    - 其他: 返回完整文本(title + ingredients + instructions)
    
    参数:
    embedder - 句子编码器模型
    vector_store - 包含文档嵌入向量的存储
    query - 搜索查询
    k - 返回结果数量
    min_similarity - 最小相似度阈值
    
    返回:
    list - 相关文档或属性列表
    """
    # 解析查询中的属性
    query_lower = query.lower()
    attribute = None
    
    # 检查查询是否包含属性
    attributes = ['ingredients', 'instructions', 'notes', 'serving size']
    base_query = query_lower
    
    for attr in attributes:
        if query_lower.endswith(' ' + attr):
            attribute = attr.replace(' ', '_')  # 处理'serving size'的情况
            base_query = query_lower[:-len(' ' + attr)].strip()
            break
    
    # 获取查询的嵌入向量
    query_embedding = embedder.encode(base_query, convert_to_numpy=True).reshape(1, -1)
    
    # 计算所有文档的相似度得分
    results_with_scores = []
    
    for doc in vector_store:
        # 计算标题的相似度
        title = doc['metadata']['title']
        title_lower = title.lower()
        query_tokens = [token for token in query.lower().strip().split() if token]

        title_embedding = embedder.encode(title, convert_to_numpy=True).reshape(1, -1)
        title_similarity = float(cosine_similarity(query_embedding, title_embedding)[0][0])
        # print(title_similarity)
        # 计算文档内容的相似度
        doc_embedding = doc['embedding'].reshape(1, -1)
        doc_similarity = float(cosine_similarity(query_embedding, doc_embedding)[0][0])
        # print(doc_similarity)
        # 计算最终相似度分数
        similarity = title_similarity * 0.15 + doc_similarity * 0.85
        # 如果 query 的 token 有出现在 title 的 token 中，加分
        match_count = sum(token in title_lower for token in query_tokens)
        similarity += match_count * 0.2

        results_with_scores.append((similarity, doc))


    # 按相似度降序排序
    results_with_scores.sort(reverse=True, key=lambda x: x[0])
    # 筛选相似度高于阈值的结果
    filtered_results = [(score, doc) for score, doc in results_with_scores if score >= min_similarity]

    # 如果没有找到匹配的文档
    if not filtered_results:
        return ['No matching documents!']
    
    # 获取前k个结果
    top_k_results = filtered_results[:k]
    
    # 根据属性返回结果
    final_results = []
    for _, doc in top_k_results:
        if attribute:
            # 如果请求特定属性
            if attribute in doc['metadata']:
                final_results.append(doc['metadata'][attribute])
        else:
            # 如果没有指定属性,返回完整文本
            title = doc['metadata']['title']
            ingredients = doc['metadata'].get('ingredients', '')
            instructions = doc['metadata'].get('instructions', '')
            full_text = f"{title}\n{ingredients}\n{instructions}".strip()
            final_results.append(full_text)
    
    # 如果没有结果,返回No matching documents
    if not final_results:
        return ['No matching documents!']
        
    return final_results

def normalize(text):
    return re.sub(r'\s+', ' ', text.strip())

k = 3
min_similarity = 0.8

#测试代码
test_cases = [
    ('TUNA BROCCOLI CASSEROLE notes', 0, 'notes', 'Broccoli right in your biscuits!'),
              ('Fruit Short Pie ingredients', 0, 'ingredients', '2 tbsp. Bisquick\n1 cup sugar\n½ tsp. cinnamon\n1 cup water\n1 tbsp. lemon juice\n4 cups fresh blueberries, peaches, or cherries'),
              ('watermelon', 0, 'text', 'No matching documents!'),
              ('SWEDISH PANCAKES instructions', 0, 'instructions', 'Beat together until blended. Lightly grease a 6 or 7″ skillet. Spoon about 3 tbsp. batter into hot skillet and tilt to coat bottom of pan. Cook until small bubbles appear on surface. Loosen edges with spatula, turn pancake gently and finish baking on other side. Lay on towel or absorbent paper; place in low oven to keep warm. Spread each with sugar, jam, applesauce, or whipped cream, etc. and roll up like jelly roll. Serve warm. Makes about 15.'),
              ('DEVILED HAM TURNOVERS', 0, 'text', 'DEVILED HAM TURNOVERS\nHeat oven to 450° (hot). Make Biscuit or Fruit Shortcake dough (p. 3). Roll into 15″ square on surface lightly dusted with Bisquick. Cut into twenty-five 3″ squares. Place on ungreased baking sheet. Spoon a little Ham Filling onto center of each square. Make triangle by folding one half over the other so top edge slightly overlaps. Press edges together with a fork dipped in cold water. Bake 8 to 10 min. Ham Filling: Blend two 2¼-oz. cans deviled ham and 2 tbsp. cream.'),
              ('cranberry muffin ingredients', 0, 'ingredients', '¾ cup raw cranberries (cut in halves or quarters) ½ cup confectioners’ sugar'),
              ('vanilla pudding', 0, 'text', 'No matching documents!'),
              ('strawberry pie', 0, 'text', 'STRAWBERRY GLACÉ SHORT PIE\n1 qt. strawberries\n1 cup water\n1 cup sugar\n3 tbsp. cornstarch\nWash, drain, and hull strawberries. For glaze, simmer 1 cup of the berries with ⅔ cup water until berries start to break up (about 3 min.). Blend sugar, cornstarch, remaining ⅓ cup water; stir into boiling mixture. Boil 1 min., stirring constantly. Cool. Pour remaining 3 cups of berries into baked Short Pie (p. 8). Cover with glaze. Refrigerate until firm ... about 2 hr. Top with whipped cream or ice cream.'),
              ('coffee cake', 2, 'text', 'BANANA COFFEE CAKE Make Coffee Cake batter (p. 2)—except add 1 cup mashed, fully ripe bananas in place of milk. Bake.'),
              ('noodles notes', 0, 'notes', 'A new easier way to make real homemade noodles.'),
              ('helicopter ingredients', 0, 'text', 'No matching documents!'),
              ('WHUFFINS', 0, 'instructions', 'WHUFFINS Make richer Muffins (p. 2)—except fold 1½ cups Wheaties carefully into batter.'),
              ('asparagus cake serving size', 0, 'serving size', [6,6]),
              ('cinnamon doughnuts ingredients', 0, 'ingredients', '2 cups Bisquick\n¼ cup sugar\n⅓ cup milk\n1 tsp. vanilla\n1 egg\n¼ tsp. each cinnamon\nnutmeg, if desired'),
              ('pineapple buns', 0, 'text', 'PINEAPPLE STICKY BUNS ¾ cup drained crushed pineapple\n½ cup soft butter\n½ cup brown sugar (packed)\n1 tsp. cinnamon Heat oven to 425° (hot). Mix ingredients and divide among 12 large greased muffin cups. Make Fruit Shortcake dough (p. 3). Spoon over pineapple mixture. Bake 15 to 20 min. Invert on tray or rack immediately to prevent sticking to pans.')
              ]
score = 0
for (query, k_index, detail, expected_result) in test_cases:
  results = search(embedder, vector_store, query, k=k, min_similarity=min_similarity)#, verbose=False)
  print(f'Test case: "{query}"')
  try:
    result = normalize(results[k_index])
    expected_result = normalize(expected_result)
    if result == expected_result:
      score += 1
      print('PASSED')
    else:
      print(f'FAILED: returned incorrect {detail}')
      print('Returned: ', result)
      print('Expected: ', expected_result)
  except AttributeError:
    if results[k_index] == expected_result:
      score += 1
      print('PASSED')
    else:
      print(f'FAILED: returned incorrect serving size')
      print('Returned: ', results[k_index])
      print('Expected: ', expected_result)
  except IndexError:
      result_str = 'results' if k_index > 1 else 'result'
      print(f'FAILED: the query "{query}" returned less than {k_index+1} {result_str}')
  print('------')
print(f'Score: {score}/{len(test_cases)}')