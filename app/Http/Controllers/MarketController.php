<?php

namespace App\Http\Controllers;

use App\Models\Stock;
use App\Service\StockService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Inertia\Inertia;
use Inertia\Response;

class MarketController extends Controller
{
    /**
     * Show the user's profile settings page.
     */
    public function index(Request $request): Response
    {
        $stocks = Stock::all();
        return Inertia::render('markets/page', [
            'stocks' => $stocks,
        ]);
    }
    /**
     * Show the user's profile settings page.
     */
    public function details(Request $request, StockService $stockService, Stock $stock): Response
    {
        $stockPrices = $stock->prices()->orderBy('date', 'desc')->limit(60)->get();
        $stockImage = $stock->images()->where('type', 'model')->where('stock_id', $stock->id)->orderBy('date', 'desc')->first();

        $uuid = $stockService->getLastUuidData(1);
        $forecast = $stock->forecasts()->where('uuid', $uuid)->orderBy('date', 'desc')->get();

        return Inertia::render('markets/details', [
            'stock' => $stock,
            'stockPrices' => $stockPrices,
            'stockImage' =>  Storage::disk('public')->url('images/' .$stockImage->image),
            'forecast' => $forecast
        ]);
    }
}
