import pytest
import asyncio
import time


@pytest.mark.performance
@pytest.mark.slow
class TestPerformance:
    """Тесты производительности."""

    async def test_concurrent_url_creation(
        self,
        async_client,
        benchmark,
    ):
        """Тестируем создание URL в конкурентном режиме."""
        async def create_url(i: int):
            url_data = {'original_url': f'https://performance-test-{i}.com'}
            response = await async_client.post('/', json=url_data)
            return response.status_code
        
        tasks = [create_url(i) for i in range(50)]
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        
        success_count = sum(1 for r in results if r == 200)
        error_count = sum(1 for r in results if isinstance(r, Exception))
        
        print(f"🎯 Performance: {len(tasks)} requests in {total_time:.4f}s "
              f"({success_count} success, {error_count} errors)")
        
        assert success_count >= 45
        assert total_time < 5.0

    async def test_high_redirect_load(
        self,
        async_client,
        url_factory,
    ):
        """Тестируем нагрузку редиректов."""
        short_url = await url_factory()
        
        async def perform_redirect():
            response = await async_client.get(
                f"/{short_url.short_code}",
                follow_redirects=False
            )
            return response.status_code
        
        tasks = [perform_redirect() for _ in range(100)]
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        success_count = sum(1 for r in results if r == 302)
        
        print(f"🎯 Redirect performance: {len(tasks)} redirects in {total_time:.4f}s "
              f"({success_count} success)")
        
        assert success_count >= 95
        assert total_time < 3.0

    async def test_mixed_workload(
        self,
        async_client,
        url_factory,
    ):
        """Тест смешанной нагрузки (создание + редиректы)."""
        created_short_codes = []
        
        async def mixed_operation(i: int):
            if i % 2 == 0:
                url_data = {'original_url': f'https://mixed-workload-{i}.com'}
                response = await async_client.post('/', json=url_data)
                if response.status_code == 200:
                    data = response.json()
                    created_short_codes.append(data['short_code'])
                return response.status_code
            else:
                if created_short_codes:
                    short_code = created_short_codes[-1]
                    response = await async_client.get(f'/{short_code}', follow_redirects=False)
                    return response.status_code
                return 0
        
        tasks = [mixed_operation(i) for i in range(30)]
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        
        success_count = sum(1 for r in results if r in [200, 302])
        
        print(f"🎯 Mixed workload: {len(tasks)} operations in {total_time:.4f}s "
              f"({success_count} success)")
        
        assert success_count >= 25
        assert total_time < 4.0


@pytest.mark.load
class TestLoadTesting:
    """Нагрузочное тестирование."""
    
    async def test_sustained_throughput(self, async_client, url_factory):
        """Тест устойчивой пропускной способности."""
        short_url = await url_factory()
        
        request_count = 0
        error_count = 0
        duration = 5
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                response = await async_client.get(
                    f"/{short_url.short_code}", 
                    follow_redirects=False
                )
                if response.status_code == 302:
                    request_count += 1
                else:
                    error_count += 1
            except Exception:
                error_count += 1
            
            await asyncio.sleep(0.01)
        
        total_time = time.time() - start_time
        rps = request_count / total_time
        
        print(f"🚀 Load test: {request_count} requests in {total_time:.2f}s "
              f"({rps:.2f} RPS, {error_count} errors)")
        
        assert rps > 10
        assert error_count < request_count * 0.1
