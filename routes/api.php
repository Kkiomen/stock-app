<?php

use App\Http\Controllers\Api\StockController;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

Route::get('/user', function (Request $request) {
    return $request->user();
})->middleware('auth:sanctum');


Route::post('stock-api', [StockController::class, 'create'])
    ->name('stock-api');

Route::post('stock-api/image', [StockController::class, 'image'])
    ->name('stock-api-image');

Route::post('stock-api/forecast', [StockController::class, 'forecast'])
    ->name('stock-api-forecast');

// Grupa tras dla analizy giełdowej
Route::prefix('stock-analysis')->group(function () {

    // Synchroniczne uruchomienie analizy
    Route::post('/run', [StockController::class, 'runStockAnalysis']);

    // Asynchroniczne uruchomienie analizy (przez Queue)
    Route::post('/run-async', [StockController::class, 'runStockAnalysisAsync']);

    // Uruchomienie przez HTTP API (jeśli Python będzie miał serwer HTTP)
    Route::post('/run-api', [StockController::class, 'runStockAnalysisViaAPI']);
    Route::post('/run-api/clear/{stock}', [StockController::class, 'runStockAnalysisViaCleanAPI']);

});
