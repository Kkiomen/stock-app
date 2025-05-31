<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\User;
use App\Service\StockImageService;
use App\Service\StockService;
use Illuminate\Auth\Events\Registered;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Log;
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;
use Illuminate\Support\Facades\Storage;
use Illuminate\Validation\Rules;
use Inertia\Inertia;
use Inertia\Response;
use Illuminate\Http\JsonResponse;

class StockController extends Controller
{
    /**
     * Uruchom analizę akcji/krypto
     */
    public function runStockAnalysis(Request $request)
    {
        // Walidacja parametrów
        $validated = $request->validate([
            'ticker' => 'required|string|max:20',
            'start_date' => 'required|date|before:today',
            'test_size_pct' => 'numeric|min:0.05|max:0.5',
            'forecast_days' => 'integer|min:1|max:90'
        ]);

        // Domyślne wartości
        $ticker = $validated['ticker'];
        $trends = $validated['trends'];
        $startDate = $validated['start_date'];
        $testSizePct = $validated['test_size_pct'] ?? 0.15;
        $forecastDays = $validated['forecast_days'] ?? 20;

        try {
            // Sposób 1: Uruchomienie przez docker exec
            $result = $this->runDockerAnalysis($ticker, $trends, $startDate, $testSizePct, $forecastDays);

            return response()->json([
                'success' => true,
                'message' => 'Analiza została uruchomiona pomyślnie',
                'data' => $result
            ]);

        } catch (\Exception $e) {
            Log::error('Stock analysis error: ' . $e->getMessage());

            return response()->json([
                'success' => false,
                'message' => 'Błąd podczas uruchamiania analizy',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Metoda 1: Uruchomienie przez docker exec
     */
    private function runDockerAnalysis($ticker, $trends, $startDate, $testSizePct, $forecastDays)
    {
        $command = [
            'docker', 'exec', 'stock-python',
            'python', '/app/stock_model.py',
            '--ticker', $ticker,
            '--trends', $trends,
            '--start_date', $startDate,
            '--test_size_pct', (string)$testSizePct,
            '--forecast_days', (string)$forecastDays
        ];

        $process = new Process($command);
        $process->setTimeout(300.0); // 5 minut timeout
        $process->run();

        if (!$process->isSuccessful()) {
            throw new ProcessFailedException($process);
        }

        return [
            'output' => $process->getOutput(),
            'execution_time' => $process->getTimeout()
        ];
    }

    /**
     * Metoda 2: Uruchomienie przez HTTP request do Python API
     */
    public function runStockAnalysisViaAPI(Request $request)
    {

        $validated = $request->validate([
            'ticker' => 'required|string|max:20',
            'trends' => 'required|string|max:30',
            'start_date' => 'required|date|before:today',
            'test_size_pct' => 'numeric|min:0.05|max:0.5',
            'forecast_days' => 'integer|min:1|max:90'
        ]);


        try {
            $client = new \GuzzleHttp\Client();
            $response = $client->post('http://stock-python:8000/analyze', [
                'json' => $validated,
                'timeout' => 300
            ]);

            $result = json_decode($response->getBody()->getContents(), true);

            return response()->json([
                'success' => true,
                'data' => $result
            ]);

        } catch (\Exception $e) {
            Log::error('Stock analysis API error: ' . $e->getMessage());

            return response()->json([
                'success' => false,
                'message' => 'Błąd podczas komunikacji z Python API',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Metoda 3: Asynchroniczne uruchomienie przez Queue
     */
    public function runStockAnalysisAsync(Request $request)
    {
        $validated = $request->validate([
            'ticker' => 'required|string|max:20',
            'trends' => 'required|string|max:30',
            'start_date' => 'required|date|before:today',
            'test_size_pct' => 'numeric|min:0.05|max:0.5',
            'forecast_days' => 'integer|min:1|max:90'
        ]);

        // Uruchom job w tle
        \App\Jobs\StockAnalysisJob::dispatch($validated);

        return response()->json([
            'success' => true,
            'message' => 'Analiza została dodana do kolejki wykonania'
        ]);
    }


    public function create(Request $request, StockService $stockService): JsonResponse
    {
        $data = $request->all();

        $stock = $stockService->getOrCreateByTicker($data['ticker']);
        $stockService->savePrices($stock, $data);

        return response()->json([
            'data' => $data
        ]);
    }

    public function image(Request $request, StockService $stockService): JsonResponse
    {
        $data = $request->all();

        $stock = $stockService->getOrCreateByTicker($data['ticker']);
        $stockImage = $stockService->saveImages($stock, $data);

        return response()->json([
            'data' => $data,
            'stockImage' => $stockImage
        ]);
    }

    public function forecast(Request $request, StockService $stockService): JsonResponse
    {
        $data = $request->all();

        $stock = $stockService->getOrCreateByTicker($data['ticker']);
        $stockForecasts = $stockService->saveForecasts($stock, $data);


        return response()->json([
            'message' => 'Stock creation endpoint',
            'data' => $data,
            'stockForecast' => $stockForecasts
        ]);
    }
}
