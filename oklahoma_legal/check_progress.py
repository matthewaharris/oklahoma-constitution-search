import json
p = json.load(open('embedding_progress.json'))
print(f'Processed: {len(p["processed_ids"]):,} documents')
print(f'Total cost: ${p["total_cost"]:.2f}')
