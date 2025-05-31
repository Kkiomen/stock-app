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
