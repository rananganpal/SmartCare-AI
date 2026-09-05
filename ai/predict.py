"""Lightweight AI/optimization layer for the prototype.
Replace the heuristic with a trained scikit-learn model after collecting hospital data.
"""
def recommend_slot(load_by_slot):
    return min(load_by_slot, key=load_by_slot.get)

if __name__=="__main__":
    demo={"09:20 AM":32,"10:10 AM":24,"11:40 AM":8,"12:20 PM":13}
    print("Recommended:", recommend_slot(demo))
