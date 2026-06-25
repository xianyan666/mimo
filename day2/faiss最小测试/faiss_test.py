"""
FAISS最小测试：学习基础使用、性能优化和算法原理
覆盖：基本搜索、多种索引、距离度量、持久化
"""

import numpy as np
import time
import faiss

def generate_data(d=64, nb=100000, nq=1000):
    """生成测试数据"""
    np.random.seed(1234)
    xb = np.random.random((nb, d)).astype('float32')
    xb[:, 0] += np.arange(nb) / 1000.
    xq = np.random.random((nq, d)).astype('float32')
    xq[:, 0] += np.arange(nq) / 1000.
    return xb, xq

def test_flat_index(xb, xq, k=4):
    """测试Flat索引（暴力搜索）"""
    print("\n" + "="*50)
    print("1. Flat索引（暴力搜索）")
    print("="*50)
    
    d = xb.shape[1]
    
    # L2距离
    print("\n[1.1] L2距离（欧氏距离）")
    index_l2 = faiss.IndexFlatL2(d)
    print(f"索引是否已训练: {index_l2.is_trained}")
    index_l2.add(xb)
    print(f"索引中的向量数量: {index_l2.ntotal}")
    
    start = time.time()
    D, I = index_l2.search(xq[:5], k)
    elapsed = time.time() - start
    print(f"搜索耗时: {elapsed:.4f}秒")
    print(f"最近邻索引:\n{I}")
    print(f"对应距离:\n{D}")
    
    # 内积
    print("\n[1.2] 内积（相似度）")
    index_ip = faiss.IndexFlatIP(d)
    index_ip.add(xb)
    
    start = time.time()
    D, I = index_ip.search(xq[:5], k)
    elapsed = time.time() - start
    print(f"搜索耗时: {elapsed:.4f}秒")
    print(f"最近邻索引:\n{I}")
    print(f"内积值:\n{D}")
    
    # 余弦相似度（通过归一化向量）
    print("\n[1.3] 余弦相似度（归一化后内积）")
    xb_norm = xb.copy()
    faiss.normalize_L2(xb_norm)
    xq_norm = xq.copy()
    faiss.normalize_L2(xq_norm)
    
    index_cosine = faiss.IndexFlatIP(d)
    index_cosine.add(xb_norm)
    
    start = time.time()
    D, I = index_cosine.search(xq_norm[:5], k)
    elapsed = time.time() - start
    print(f"搜索耗时: {elapsed:.4f}秒")
    print(f"最近邻索引:\n{I}")
    print(f"余弦相似度:\n{D}")
    
    return index_l2

def test_ivf_index(xb, xq, k=4):
    """测试IVF索引（倒排文件索引）"""
    print("\n" + "="*50)
    print("2. IVF索引（倒排文件索引）")
    print("="*50)
    
    d = xb.shape[1]
    nlist = 100  # 聚类中心数量
    
    # 创建量化器
    quantizer = faiss.IndexFlatL2(d)
    
    # IVF索引需要训练
    print("\n[2.1] IVF-Flat索引")
    index_ivf = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_L2)
    print(f"索引是否已训练: {index_ivf.is_trained}")
    
    # 训练索引
    start = time.time()
    index_ivf.train(xb)
    train_time = time.time() - start
    print(f"训练耗时: {train_time:.4f}秒")
    print(f"索引是否已训练: {index_ivf.is_trained}")
    
    # 添加向量
    start = time.time()
    index_ivf.add(xb)
    add_time = time.time() - start
    print(f"添加耗时: {add_time:.4f}秒")
    print(f"索引中的向量数量: {index_ivf.ntotal}")
    
    # 设置搜索时检查的聚类数量
    index_ivf.nprobe = 10  # 默认是1，增加可提高精度但降低速度
    
    # 搜索
    start = time.time()
    D, I = index_ivf.search(xq[:5], k)
    search_time = time.time() - start
    print(f"搜索耗时: {search_time:.4f}秒")
    print(f"最近邻索引:\n{I}")
    print(f"对应距离:\n{D}")
    
    return index_ivf

def test_hnsw_index(xb, xq, k=4):
    """测试HNSW索引（分层可导航小世界图）"""
    print("\n" + "="*50)
    print("3. HNSW索引（分层可导航小世界图）")
    print("="*50)
    
    d = xb.shape[1]
    M = 32  # 每个节点的连接数
    efConstruction = 40  # 构建时的搜索范围
    efSearch = 16  # 搜索时的搜索范围
    
    print("\n[3.1] HNSW索引")
    index_hnsw = faiss.IndexHNSWFlat(d, M)
    index_hnsw.hnsw.efConstruction = efConstruction
    index_hnsw.hnsw.efSearch = efSearch
    
    # HNSW不需要显式训练
    print(f"索引是否已训练: {index_hnsw.is_trained}")
    
    # 添加向量
    start = time.time()
    index_hnsw.add(xb)
    add_time = time.time() - start
    print(f"添加耗时: {add_time:.4f}秒")
    print(f"索引中的向量数量: {index_hnsw.ntotal}")
    
    # 搜索
    start = time.time()
    D, I = index_hnsw.search(xq[:5], k)
    search_time = time.time() - start
    print(f"搜索耗时: {search_time:.4f}秒")
    print(f"最近邻索引:\n{I}")
    print(f"对应距离:\n{D}")
    
    return index_hnsw

def test_pq_index(xb, xq, k=4):
    """测试PQ索引（乘积量化）"""
    print("\n" + "="*50)
    print("4. PQ索引（乘积量化）")
    print("="*50)
    
    d = xb.shape[1]
    m = 8  # 子量化器数量
    nbits = 8  # 每个子量化器的位数
    
    print("\n[4.1] PQ索引")
    index_pq = faiss.IndexPQ(d, m, nbits)
    
    # PQ需要训练
    print(f"索引是否已训练: {index_pq.is_trained}")
    
    # 训练索引
    start = time.time()
    index_pq.train(xb)
    train_time = time.time() - start
    print(f"训练耗时: {train_time:.4f}秒")
    print(f"索引是否已训练: {index_pq.is_trained}")
    
    # 添加向量
    start = time.time()
    index_pq.add(xb)
    add_time = time.time() - start
    print(f"添加耗时: {add_time:.4f}秒")
    print(f"索引中的向量数量: {index_pq.ntotal}")
    
    # 搜索
    start = time.time()
    D, I = index_pq.search(xq[:5], k)
    search_time = time.time() - start
    print(f"搜索耗时: {search_time:.4f}秒")
    print(f"最近邻索引:\n{I}")
    print(f"对应距离:\n{D}")
    
    return index_pq

def test_ivfpq_index(xb, xq, k=4):
    """测试IVF+PQ索引（倒排文件+乘积量化）"""
    print("\n" + "="*50)
    print("5. IVF+PQ索引（倒排文件+乘积量化）")
    print("="*50)
    
    d = xb.shape[1]
    nlist = 100
    m = 8
    nbits = 8
    
    # 创建量化器
    quantizer = faiss.IndexFlatL2(d)
    
    print("\n[5.1] IVF+PQ索引")
    index_ivfpq = faiss.IndexIVFPQ(quantizer, d, nlist, m, nbits)
    
    # 需要训练
    print(f"索引是否已训练: {index_ivfpq.is_trained}")
    
    # 训练索引
    start = time.time()
    index_ivfpq.train(xb)
    train_time = time.time() - start
    print(f"训练耗时: {train_time:.4f}秒")
    print(f"索引是否已训练: {index_ivfpq.is_trained}")
    
    # 添加向量
    start = time.time()
    index_ivfpq.add(xb)
    add_time = time.time() - start
    print(f"添加耗时: {add_time:.4f}秒")
    print(f"索引中的向量数量: {index_ivfpq.ntotal}")
    
    # 设置搜索时检查的聚类数量
    index_ivfpq.nprobe = 10
    
    # 搜索
    start = time.time()
    D, I = index_ivfpq.search(xq[:5], k)
    search_time = time.time() - start
    print(f"搜索耗时: {search_time:.4f}秒")
    print(f"最近邻索引:\n{I}")
    print(f"对应距离:\n{D}")
    
    return index_ivfpq

def test_persistence(index, xb, xq, index_name="index"):
    """测试索引的持久化（保存和加载）"""
    print("\n" + "="*50)
    print(f"6. 持久化测试（{index_name}）")
    print("="*50)
    
    # 保存索引
    filename = f"{index_name}.faiss"
    start = time.time()
    faiss.write_index(index, filename)
    save_time = time.time() - start
    print(f"保存索引到 {filename}，耗时: {save_time:.4f}秒")
    
    # 加载索引
    start = time.time()
    loaded_index = faiss.read_index(filename)
    load_time = time.time() - start
    print(f"加载索引从 {filename}，耗时: {load_time:.4f}秒")
    
    # 验证加载的索引
    print(f"加载的索引中的向量数量: {loaded_index.ntotal}")
    
    # 比较搜索结果
    k = 4
    D1, I1 = index.search(xq[:5], k)
    D2, I2 = loaded_index.search(xq[:5], k)
    
    if np.array_equal(I1, I2):
        print("[OK] 搜索结果一致")
    else:
        print("[FAIL] 搜索结果不一致")
    
    return loaded_index

def compare_performance(xb, xq, k=4):
    """比较不同索引的性能"""
    print("\n" + "="*50)
    print("7. 性能比较")
    print("="*50)
    
    d = xb.shape[1]
    nq = xq.shape[0]
    
    # 测试不同索引
    indices = {
        "Flat (暴力搜索)": faiss.IndexFlatL2(d),
        "IVF-Flat (nlist=100)": faiss.IndexIVFFlat(faiss.IndexFlatL2(d), d, 100),
        "HNSW (M=32)": faiss.IndexHNSWFlat(d, 32),
        "PQ (m=8, nbits=8)": faiss.IndexPQ(d, 8, 8),
        "IVF-PQ (nlist=100, m=8)": faiss.IndexIVFPQ(faiss.IndexFlatL2(d), d, 100, 8, 8)
    }
    
    results = {}
    
    for name, index in indices.items():
        print(f"\n测试 {name}...")
        
        # 训练（如果需要）
        if not index.is_trained:
            start = time.time()
            index.train(xb)
            train_time = time.time() - start
            print(f"  训练耗时: {train_time:.4f}秒")
        
        # 添加向量
        start = time.time()
        index.add(xb)
        add_time = time.time() - start
        print(f"  添加耗时: {add_time:.4f}秒")
        
        # 搜索
        start = time.time()
        D, I = index.search(xq, k)
        search_time = time.time() - start
        print(f"  搜索耗时: {search_time:.4f}秒")
        
        results[name] = {
            "train_time": train_time if not index.is_trained else 0,
            "add_time": add_time,
            "search_time": search_time
        }
    
    # 打印比较表格
    print("\n" + "="*80)
    print("性能比较汇总")
    print("="*80)
    print(f"{'索引类型':<30} {'训练耗时':<12} {'添加耗时':<12} {'搜索耗时':<12}")
    print("-"*80)
    for name, times in results.items():
        print(f"{name:<30} {times['train_time']:<12.4f} {times['add_time']:<12.4f} {times['search_time']:<12.4f}")

def explain_algorithms():
    """解释不同索引算法的原理"""
    print("\n" + "="*50)
    print("8. 算法原理解释")
    print("="*50)
    
    explanations = {
        "Flat (暴力搜索)": """
原理：直接计算查询向量与所有数据库向量的距离
优点：精确搜索，无误差
缺点：速度慢，时间复杂度O(n*d)
适用：小数据集或需要精确结果的场景
""",
        "IVF (倒排文件索引)": """
原理：先将向量空间划分为nlist个聚类，搜索时只检查最近的nprobe个聚类
优点：大幅减少搜索范围，速度提升
缺点：需要训练，可能漏掉一些近邻
参数：nlist（聚类数量）、nprobe（搜索时检查的聚类数量）
""",
        "HNSW (分层可导航小世界图)": """
原理：构建多层图结构，每层都是一个小世界图，搜索时从顶层开始逐层下降
优点：搜索速度快，精度高
缺点：内存占用大，构建时间长
参数：M（每个节点的连接数）、efConstruction（构建时的搜索范围）、efSearch（搜索时的搜索范围）
""",
        "PQ (乘积量化)": """
原理：将高维向量分成m个子空间，每个子空间用nbits位的码本表示
优点：内存占用小，适合大规模数据
缺点：有精度损失，需要训练
参数：m（子量化器数量）、nbits（每个子量化器的位数）
""",
        "IVF+PQ (倒排文件+乘积量化)": """
原理：结合IVF和PQ，先用IVF缩小搜索范围，再用PQ进行近似距离计算
优点：兼顾速度和内存，适合大规模数据
缺点：需要训练，精度有损失
参数：nlist、m、nbits
"""
    }
    
    for name, explanation in explanations.items():
        print(f"\n{name}:")
        print(explanation)

def main():
    print("FAISS最小测试：学习基础使用、性能优化和算法原理")
    print("="*50)
    
    # 生成测试数据
    d = 64  # 向量维度
    nb = 100000  # 数据库大小
    nq = 1000  # 查询数量
    
    print(f"生成测试数据: 维度={d}, 数据库大小={nb}, 查询数量={nq}")
    xb, xq = generate_data(d, nb, nq)
    
    # 测试不同索引
    index_flat = test_flat_index(xb, xq)
    index_ivf = test_ivf_index(xb, xq)
    index_hnsw = test_hnsw_index(xb, xq)
    index_pq = test_pq_index(xb, xq)
    index_ivfpq = test_ivfpq_index(xb, xq)
    
    # 测试持久化
    test_persistence(index_flat, xb, xq, "flat_index")
    test_persistence(index_ivf, xb, xq, "ivf_index")
    
    # 性能比较
    compare_performance(xb, xq)
    
    # 算法原理解释
    explain_algorithms()
    
    print("\n" + "="*50)
    print("测试完成！")
    print("="*50)
    print("\n学习建议：")
    print("1. 从Flat索引开始理解基本概念")
    print("2. 尝试调整IVF的nprobe参数观察精度和速度的变化")
    print("3. 比较不同索引的内存占用和搜索速度")
    print("4. 在实际数据集上测试不同索引的性能")

if __name__ == "__main__":
    main()