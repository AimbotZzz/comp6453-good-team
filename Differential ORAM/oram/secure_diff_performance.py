import time
import sys
import os
import json
from datetime import datetime
import math

# 路径设置：导入 oram 实现
THIS_DIR = os.path.dirname(__file__)
ORAM_DIR = os.path.join(THIS_DIR, 'oram')
sys.path.append(ORAM_DIR)

# 导入三种实现
from oram_readpath import ORAMReadPath as FullPathORAM
from differential_write_back import ORAMReadPath as DifferentialORAM
from secure_oram import SecureORAM
from bucket import Bucket


class ImplSpec:
    def __init__(self, key: str, label: str, ctor, init_kwargs_extra=None):
        self.key = key
        self.label = label
        self.ctor = ctor
        self.init_kwargs_extra = init_kwargs_extra or {}


class PerformanceRunner:
    def __init__(self):
        self.results = {
            'full_path': [],
            'differential': [],
            'secure_differential': [],
            'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _run_single(self, impl: ImplSpec, num_blocks: int, tree_height: int, bucket_size: int,
                     num_operations: int) -> dict:
        # 重置 Bucket 配置
        Bucket.reset()

        # 初始化实例（ServerStorage 内会设置 bucket_size）
        start_time = time.time()
        oram = impl.ctor(num_blocks=num_blocks, tree_height=tree_height, bucket_size=bucket_size,
                         **impl.init_kwargs_extra)
        init_time = time.time() - start_time

        # 写入测试：对每个 block 写入一次
        write_start = time.time()
        for i in range(num_blocks):
            oram.access('write', i, [i, i * 10])
        write_time = time.time() - write_start

        # 读取测试：循环访问
        read_start = time.time()
        for i in range(num_operations):
            idx = i % num_blocks
            oram.access('read', idx)
        read_time = time.time() - read_start

        # 混合测试：交替读写
        mixed_start = time.time()
        for i in range(num_operations):
            idx = i % num_blocks
            if i % 2 == 0:
                oram.access('write', idx, [idx + i, idx * i])
            else:
                oram.access('read', idx)
        mixed_time = time.time() - mixed_start

        final_stash_size = len(getattr(oram, 'stash', []))

        return {
            'impl': impl.key,
            'num_blocks': num_blocks,
            'tree_height': tree_height,
            'bucket_size': bucket_size,
            'num_leaves': 2 ** (tree_height - 1),
            'init_time': init_time,
            'write_time': write_time,
            'read_time': read_time,
            'mixed_time': mixed_time,
            'final_stash_size': final_stash_size,
            'avg_write_time': write_time / max(1, num_blocks),
            'avg_read_time': read_time / max(1, num_operations),
            'avg_mixed_time': mixed_time / max(1, num_operations),
        }

    def run_tests(self):
        impls = [
            ImplSpec('full_path', '全路径写回', FullPathORAM),
            ImplSpec('differential', '差分写回', DifferentialORAM),
            ImplSpec('secure_differential', '差分+伪装+Ring', SecureORAM, init_kwargs_extra={}),
        ]

        # 配置：覆盖之前小规模，同时加入“树规模很大”的场景
        test_configs = [
            # 小规模校验
            (16, 5, 4),
            (32, 6, 4),
            # 大树场景（重点）
            (32, 16, 8),
            (64, 16, 8),
            (128, 17, 8),
        ]

        print('=' * 80)
        print('Differential vs Full-path vs Secure (Dummy + Ring) Performance Test')
        print('=' * 80)

        for (num_blocks, tree_height, bucket_size) in test_configs:
            num_operations = min(num_blocks * 2, 200)
            print(f"\nConfig: blocks={num_blocks}, tree_height={tree_height}, bucket_size={bucket_size}, ops={num_operations}")

            for impl in impls:
                try:
                    result = self._run_single(impl, num_blocks, tree_height, bucket_size, num_operations)
                    self.results[impl.key].append(result)
                    print(f"  ✓ {impl.label}: read={result['avg_read_time']:.6f}s, write={result['avg_write_time']:.6f}s, stash={result['final_stash_size']}")
                except Exception as e:
                    self.results[impl.key].append({
                        'impl': impl.key,
                        'num_blocks': num_blocks,
                        'tree_height': tree_height,
                        'bucket_size': bucket_size,
                        'error': str(e),
                    })
                    print(f"  ✗ {impl.label}: {e}")

    def analyze_and_enrich(self):
        # 计算相对全路径写回的加速比
        baseline_map = {}
        for r in self.results['full_path']:
            if 'error' in r:
                continue
            key = (r['num_blocks'], r['tree_height'], r['bucket_size'])
            baseline_map[key] = r

        for impl_key in ('differential', 'secure_differential'):
            for r in self.results[impl_key]:
                if 'error' in r:
                    continue
                key = (r['num_blocks'], r['tree_height'], r['bucket_size'])
                base = baseline_map.get(key)
                if not base:
                    continue
                def speedup(b):
                    return (base[b] / r[b]) if r[b] > 0 else None
                r['speedup_read'] = speedup('avg_read_time')
                r['speedup_write'] = speedup('avg_write_time')
                r['speedup_mixed'] = speedup('avg_mixed_time')

    def save(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_filename = f"diff_secure_performance_results_{timestamp}.json"
        txt_filename = f"diff_secure_performance_report_{timestamp}.txt"

        with open(os.path.join(THIS_DIR, json_filename), 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"Saved results to: {json_filename}")

        # 文本报告（简要）
        lines = []
        lines.append("Differential ORAM Performance Report\n")
        lines.append('=' * 80 + "\n")
        lines.append(f"Test time: {self.results['test_time']}\n\n")

        def fmt_speedup(val):
            return f"{val:.2f}x" if isinstance(val, (int, float)) and val is not None else "-"

        for impl_key, label in [('full_path', 'Full-path'),
                                ('differential', 'Differential'),
                                ('secure_differential', 'Differential + Dummy + Ring')]:
            lines.append(f"[{label}]\n")
            for r in self.results[impl_key]:
                if 'error' in r:
                    lines.append(f"  Config blocks={r['num_blocks']}, H={r['tree_height']}, B={r['bucket_size']}: ERROR {r['error']}\n")
                    continue
                lines.append(
                    f"  Config blocks={r['num_blocks']}, H={r['tree_height']}, B={r['bucket_size']}:\n"
                    f"    read={r['avg_read_time']*1000:.3f}ms, write={r['avg_write_time']*1000:.3f}ms, mixed={r['avg_mixed_time']*1000:.3f}ms, stash={r['final_stash_size']}\n"
                )
                if impl_key != 'full_path':
                    lines.append(
                        f"    Speedup (vs Full-path): read={fmt_speedup(r.get('speedup_read'))}, write={fmt_speedup(r.get('speedup_write'))}, mixed={fmt_speedup(r.get('speedup_mixed'))}\n"
                    )
            lines.append("\n")

        with open(os.path.join(THIS_DIR, txt_filename), 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Text report saved to: {txt_filename}")


def main():
    runner = PerformanceRunner()
    runner.run_tests()
    runner.analyze_and_enrich()
    runner.save()


if __name__ == '__main__':
    main()

